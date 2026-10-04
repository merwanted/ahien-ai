"""Excel verisini RAG için akıllı chunk'lara dönüştürür."""
import re
import openpyxl
from typing import List, Dict, Optional

def parse_list(text) -> List[str]:
    if not text or str(text) == 'None':
        return []
    return re.findall(r'\[([^\]]*)\]', str(text))

def clean(text) -> str:
    if not text:
        return ""
    text = str(text).replace('_x000D_', '\n').replace('\r\n', '\n').replace('\r', '\n')
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    return text.strip()

def trend(values: List[float]) -> str:
    if len(values) < 2:
        return "yetersiz veri"
    recent = values[-3:] if len(values) >= 3 else values
    earlier = values[:3]
    avg_r = sum(recent) / len(recent)
    avg_e = sum(earlier) / len(earlier)
    pct = (avg_r - avg_e) / avg_e * 100 if avg_e else 0
    if abs(pct) < 5:
        return "stabil"
    return "yükseliş" if pct > 0 else "düşüş"

def safe_float(v):
    try:
        return float(v)
    except:
        return None

LAB_COLS = {
    'hba1c': ('HbA1c', '%'), 'üre': ('Üre', 'mg/dL'), 'kreatinin': ('Kreatinin', 'mg/dL'),
    'bun': ('BUN', 'mg/dL'), 'alt': ('ALT', 'U/L'), 'alp': ('ALP', 'U/L'),
    'ast': ('AST', 'U/L'), 'ggt': ('GGT', 'U/L'), 'bilirubin': ('Bilirubin', 'mg/dL'),
    'potasyum': ('Potasyum', 'mEq/L'), 'kalsiyum': ('Kalsiyum', 'mg/dL'),
    'magnezyum': ('Magnezyum', 'mg/dL'), 'klor': ('Klor', 'mEq/L'),
    'albumin': ('Albumin', 'g/dL'), 'crp': ('CRP', 'mg/L'),
    'ldh': ('LDH', 'U/L'), 'sodyum': ('Sodyum', 'mEq/L'),
}

class DataProcessor:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def process(self) -> List[Dict]:
        wb = openpyxl.load_workbook(self.filepath)
        ws = wb['Sheet1']
        headers = [cell.value for cell in ws[1]]
        hmap = {h: i for i, h in enumerate(headers)}

        def cell(row, col):
            idx = hmap.get(col)
            if idx is None:
                return None
            return ws.cell(row=row, column=idx + 1).value

        all_chunks = []
        stats = {"total": 0, "kanser": {}, "cinsiyet": {}, "ilac_count": 0, "lab_count": 0}

        for row_idx in range(2, ws.max_row + 1):
            pid = row_idx - 1
            kanser = str(cell(row_idx, 'kanser_turu') or 'Bilinmiyor')
            cinsiyet_raw = parse_list(cell(row_idx, 'cinsiyet'))
            cinsiyet = cinsiyet_raw[0] if cinsiyet_raw else 'bilinmiyor'
            dogum = str(cell(row_idx, 'doğum tarihi') or '')
            dept_list = parse_list(cell(row_idx, 'department'))
            dept = ', '.join(sorted(set(dept_list))) if dept_list else 'belirtilmemiş'
            olum_tarihi = parse_list(cell(row_idx, 'ölüm tarihi'))
            olum_str = olum_tarihi[0].split(' ')[0] if olum_tarihi else 'hayatta'
            icd_list = parse_list(cell(row_idx, 'icd10'))
            icd_unique = list(dict.fromkeys(icd_list))[:5]
            eslik = parse_list(cell(row_idx, 'eşlikedentanılar'))
            eslik_unique = list(dict.fromkeys(eslik))[:8]

            # Stats
            stats["total"] += 1
            stats["kanser"][kanser] = stats["kanser"].get(kanser, 0) + 1
            stats["cinsiyet"][cinsiyet] = stats["cinsiyet"].get(cinsiyet, 0) + 1

            meta = {"hasta_id": pid, "kanser_turu": kanser, "cinsiyet": cinsiyet, "dogum_yili": dogum}

            # --- CHUNK 1: Hasta Profili ---
            profil = f"""Hasta #{pid} - Profil
Kanser Türü: {kanser}
Cinsiyet: {cinsiyet.capitalize()}
Doğum Yılı: {dogum}
Bölüm: {dept}
Durum: {'Vefat - ' + olum_str if olum_str != 'hayatta' else 'Hayatta'}
ICD-10: {'; '.join(icd_unique) if icd_unique else 'belirtilmemiş'}
Eşlik Eden Tanılar: {'; '.join(eslik_unique) if eslik_unique else 'yok'}"""
            all_chunks.append({"text": profil, "type": "profil", **meta})

            # --- CHUNK 2: Lab Değerleri ---
            lab_lines = []
            for col_key, (name, unit) in LAB_COLS.items():
                raw = parse_list(cell(row_idx, col_key))
                vals = [v for v in (safe_float(x) for x in raw) if v is not None]
                if not vals:
                    continue
                stats["lab_count"] += len(vals)
                t = trend(vals)
                lab_lines.append(f"  {name}: Son={vals[-1]} {unit}, Min={min(vals)}, Max={max(vals)}, Ölçüm={len(vals)}, Trend={t}")

            if lab_lines:
                lab_text = f"Hasta #{pid} - Laboratuvar Değerleri\nKanser Türü: {kanser}\n" + "\n".join(lab_lines)
                all_chunks.append({"text": lab_text, "type": "lab", **meta})

            # --- CHUNK 3: İlaçlar ---
            ilac_list = parse_list(cell(row_idx, 'ilac'))
            atc_list = parse_list(cell(row_idx, 'atc kod'))
            if ilac_list:
                unique_ilac = list(dict.fromkeys(ilac_list))[:15]
                unique_atc = list(dict.fromkeys(atc_list))[:15]
                stats["ilac_count"] += len(unique_ilac)
                ilac_text = f"Hasta #{pid} - İlaç Tedavisi\nKanser Türü: {kanser}\nİlaçlar:\n"
                for i, il in enumerate(unique_ilac):
                    atc = unique_atc[i] if i < len(unique_atc) else ''
                    ilac_text += f"  - {il}" + (f" ({atc})" if atc else '') + "\n"
                all_chunks.append({"text": ilac_text.strip(), "type": "ilac", **meta})

            # --- CHUNK 4+: Epikriz (split) ---
            epikriz_raw = clean(cell(row_idx, 'epikriz'))
            if epikriz_raw:
                parts = epikriz_raw.split('\n\n')
                current = ""
                ep_idx = 0
                for part in parts:
                    if len(current) + len(part) > 1400 and current:
                        ep_idx += 1
                        header = f"Hasta #{pid} - Epikriz (Bölüm {ep_idx})\nKanser Türü: {kanser}\n\n"
                        all_chunks.append({"text": header + current.strip(), "type": "epikriz", **meta})
                        current = part
                    else:
                        current += "\n\n" + part if current else part
                if current.strip():
                    ep_idx += 1
                    header = f"Hasta #{pid} - Epikriz (Bölüm {ep_idx})\nKanser Türü: {kanser}\n\n"
                    all_chunks.append({"text": header + current.strip(), "type": "epikriz", **meta})

            # --- CHUNK 5: İşlemler ---
            islem_list = parse_list(cell(row_idx, 'işlem adı'))
            islem_tip = parse_list(cell(row_idx, 'işlem tipi'))
            if islem_list:
                unique_islem = list(dict.fromkeys(islem_list))[:10]
                islem_text = f"Hasta #{pid} - Tıbbi İşlemler\nKanser Türü: {kanser}\nİşlemler:\n"
                for isl in unique_islem:
                    islem_text += f"  - {isl}\n"
                all_chunks.append({"text": islem_text.strip(), "type": "islem", **meta})

        wb.close()
        return all_chunks, stats

def get_dataset_stats(filepath: str) -> Dict:
    """Frontend için istatistik hesapla."""
    _, stats = DataProcessor(filepath).process()
    return stats

if __name__ == "__main__":
    import config
    print("Veri işleniyor...")
    chunks, stats = DataProcessor(config.EXCEL_PATH).process()
    print(f"Toplam chunk: {len(chunks)}")
    print(f"İstatistikler: {stats}")
    for t in ['profil', 'lab', 'ilac', 'epikriz', 'islem']:
        c = sum(1 for ch in chunks if ch['type'] == t)
        print(f"  {t}: {c}")
    print("\nÖrnek profil chunk:")
    print(chunks[0]['text'][:500])
