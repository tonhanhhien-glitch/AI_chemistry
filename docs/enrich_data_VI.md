# Hướng dẫn bổ sung dữ liệu phân tử

Tài liệu này chỉ tập trung vào các **tệp mã nguồn được khuyến nghị chỉnh sửa trực tiếp** khi muốn bổ sung hoặc làm giàu dữ liệu cho từng phân tử trong phiên bản mã nguồn hiện tại.

Đối với việc bổ sung dữ liệu phân tử thông thường, nên sử dụng bốn tệp sau:

```text
backend/app/data/curated_molecules.json
backend/app/data/chemical_identities.json
backend/app/data/experimental_geometries.json
backend/app/data/curated_properties.json
```

## Thứ tự khuyến nghị

1. `curated_molecules.json` — dữ liệu cốt lõi về Lewis, VSEPR và nội dung giảng dạy.
2. `experimental_geometries.json` — độ dài liên kết, góc liên kết và tọa độ thực nghiệm đã được xác minh.
3. `chemical_identities.json` — số CAS và các tên/biệt danh dùng cho tìm kiếm.
4. `curated_properties.json` — các tính chất vật lý/hóa học đã được kiểm duyệt kèm nguồn.

---

## 1. `curated_molecules.json`

Đường dẫn:

```text
backend/app/data/curated_molecules.json
```

Thêm hoặc cập nhật phân tử bên trong mảng `molecules` ở cấp cao nhất.

Tệp này dùng để lưu:

- công thức và điện tích
- tên tiếng Anh/tiếng Việt và các tên khác
- PubChem CID và SMILES
- thành phần nguyên tử và thứ tự nguyên tử
- nguyên tử trung tâm
- tổng số electron hóa trị
- bậc liên kết trong công thức Lewis
- số cặp electron tự do
- điện tích hình thức
- cộng hưởng
- ngoại lệ quy tắc bát tử
- số miền electron theo VSEPR
- ký hiệu AXnEm
- hình học miền electron
- hình học phân tử
- góc tham khảo/giảng dạy riêng cho phân tử
- lai hóa
- độ phân cực và ghi chú giảng dạy

### Mẫu

```json
{
  "review_status": "internal_golden_pending_expert_signoff",
  "pubchem_cid": null,
  "source": "curated",
  "confidence": "high",

  "hybridization_warning_vi": "Nhãn lai hoá là mô hình sư phạm gần đúng theo VSEPR, không phải mô tả liên kết hiện đại đầy đủ.",
  "hybridization_warning_en": "The hybridization label is an approximate VSEPR-style pedagogical model, not a full modern description of bonding.",

  "three_d_source": {
    "kind": "idealized_vsepr_template",
    "verified_reference": false
  },

  "id": "molecule-id",
  "name_vi": "Tên chất",
  "name_en": "English name",
  "aliases": ["tên thường gọi"],

  "formula": "XY2",
  "charge": 0,

  "atom_inventory": {
    "X": 1,
    "Y": 2
  },

  "atom_symbols": ["X", "Y", "Y"],
  "central_atom": "X",

  "total_valence_electrons": 0,

  "bond_orders": [1, 1],
  "lone_pairs": [0, 0, 0],
  "formal_charges": [0, 0, 0],

  "resonance_forms": 1,
  "resonance_note_vi": null,

  "exception_flags": {
    "electron_deficient": false,
    "expanded_octet": false,
    "odd_electron": false
  },

  "bonding_domains": 2,
  "lone_pair_domains": 0,
  "steric_number": 2,

  "ax_en": "AX2",

  "electron_geometry": "linear",
  "molecular_geometry": "linear",
  "electron_geometry_vi": "thẳng",
  "molecular_geometry_vi": "thẳng",

  "ideal_angle": "180°",
  "distortion_note_vi": null,

  "hybridization": "sp",

  "polarity_note_vi": null,
  "polarity_note_en": null,

  "smiles": null,

  "teaching_note_vi": null,
  "teaching_note_en": null
}
```

### Các quy tắc nhất quán quan trọng

Phần tử đầu tiên của `atom_symbols` phải là nguyên tử trung tâm:

```text
atom_symbols[0] = central_atom
```

Với một phân tử có `N` nguyên tử:

```text
len(atom_symbols)   = N
len(bond_orders)    = N - 1
len(lone_pairs)     = N
len(formal_charges) = N
```

Ngoài ra:

```text
sum(formal_charges) = charge
```

Việc đếm electron trong công thức Lewis phải thỏa mãn:

```text
2 × sum(bond_orders) + 2 × sum(lone_pairs)
= total_valence_electrons
```

Các trường VSEPR phải nhất quán với nhau:

```text
bonding_domains + lone_pair_domains = steric_number
```

Liên kết đôi hoặc liên kết ba vẫn chỉ được tính là **một miền liên kết** trong VSEPR.

### Góc riêng của phân tử

`ideal_angle` có thể lưu một giá trị tham khảo ngắn gọn, riêng cho phân tử, dùng cho mục đích giảng dạy.

Ví dụ:

```json
"ideal_angle": "~107°"
```

hoặc:

```json
"ideal_angle": "~102°"
```

Các giá trị góc thực nghiệm chi tiết kèm nguồn nên được lưu trong `experimental_geometries.json`.

---

## 2. `experimental_geometries.json`

Đường dẫn:

```text
backend/app/data/experimental_geometries.json
```

Thêm dữ liệu vào mảng `records` ở cấp cao nhất.

Tệp này dùng cho hình học phân tử thực nghiệm đã được xác minh, bao gồm:

- độ dài liên kết thực nghiệm
- góc liên kết thực nghiệm
- nhiều góc không tương đương trong cùng một phân tử
- góc nhị diện
- tọa độ Descartes
- nhóm điểm
- pha
- trạng thái điện tử
- nguồn, tài liệu tham khảo và URL

Đây là nơi được khuyến nghị để lưu các giá trị hình học thực của `NH3`, `NF3`, `ClF3`, v.v.

### Mẫu

```json
{
  "id": "source-molecule-reference",
  "evidence_type": "experimental",

  "identity": {
    "formula": "XY2",
    "charge": 0,

    "atom_inventory": {
      "X": 1,
      "Y": 2
    },

    "formula_identity_unambiguous": true,

    "cas_rn": null,
    "pubchem_cid": null,
    "inchi": null,
    "inchikey": null,

    "curated_molecule_id": "molecule-id"
  },

  "units": "angstrom",

  "phase": "gas",
  "electronic_state": null,
  "conformation": "equilibrium",
  "point_group": null,

  "atoms": [
    {"id": "a0", "element": "X", "role": "center"},
    {"id": "a1", "element": "Y", "role": "ligand"},
    {"id": "a2", "element": "Y", "role": "ligand"}
  ],

  "bonds": [
    {"atom1_id": "a0", "atom2_id": "a1", "order": 1},
    {"atom1_id": "a0", "atom2_id": "a2", "order": 1}
  ],

  "bond_lengths": [
    {
      "id": "mol-r1",
      "atom1_id": "a0",
      "atom2_id": "a1",
      "value_angstrom": 1.000,
      "equivalent_count": 2,
      "label": "X-Y"
    }
  ],

  "bond_angles": [
    {
      "id": "mol-a1",
      "atom1_id": "a1",
      "center_atom_id": "a0",
      "atom2_id": "a2",
      "value_deg": 100.00,
      "equivalent_count": 1,
      "label": "Y-X-Y"
    }
  ],

  "dihedrals": [],

  "coordinates": null,

  "source": {
    "name": "Tên nguồn",
    "reference": "Mã tham khảo hoặc bài báo",
    "url": "https://example.com/source",
    "comments": "Hình học cân bằng pha khí từ dữ liệu thực nghiệm.",
    "retrieved_at": "2026-08-18T00:00:00Z"
  }
}
```

### Nhiều góc không tương đương

Giữ các góc khác nhau thành các bản ghi riêng. Không nên lấy trung bình các giá trị này.

Ví dụ với phân tử dạng chữ T:

```json
"bond_angles": [
  {
    "id": "mol-angle-1",
    "atom1_id": "a1",
    "center_atom_id": "a0",
    "atom2_id": "a2",
    "value_deg": 87.45,
    "equivalent_count": 2,
    "label": "axial-equatorial"
  },
  {
    "id": "mol-angle-2",
    "atom1_id": "a1",
    "center_atom_id": "a0",
    "atom2_id": "a3",
    "value_deg": 174.90,
    "equivalent_count": 1,
    "label": "axial-axial"
  }
]
```

Điều này đặc biệt quan trọng với các phân tử như `ClF3`, nơi góc gần 90° và góc gần 180° không tương đương nhau.

### Tọa độ

Nếu có tọa độ Descartes đã được xác minh:

```json
"coordinates": [
  {"id": "a0", "element": "X", "x": 0.0, "y": 0.0, "z": 0.0},
  {"id": "a1", "element": "Y", "x": 1.0, "y": 0.0, "z": 0.0},
  {"id": "a2", "element": "Y", "x": -0.2, "y": 0.98, "z": 0.0}
]
```

Nếu không có tọa độ đáng tin cậy:

```json
"coordinates": null
```

Mỗi `id` trong `coordinates` phải tương ứng với một nguyên tử trong `atoms`.

Chỉ sử dụng:

```json
"evidence_type": "experimental"
```

khi dữ liệu hình học thực sự có nguồn gốc thực nghiệm.

---

## 3. `chemical_identities.json`

Đường dẫn:

```text
backend/app/data/chemical_identities.json
```

Thêm dữ liệu vào mảng `identities` ở cấp cao nhất.

Tệp này dùng cho:

- công thức
- điện tích
- ID của phân tử curated
- số CAS
- tên tiếng Anh/tiếng Việt
- tên thường gọi và tên thay thế dùng trong tìm kiếm

### Mẫu

```json
{
  "formula": "XY2",
  "charge": 0,

  "curated_molecule_id": "molecule-id",

  "cas_rn": "1234-56-7",

  "names": [
    "English name",
    "Tên tiếng Việt",
    "tên thường gọi",
    "tên thay thế"
  ]
}
```

Nếu chưa xác minh được số CAS:

```json
"cas_rn": null
```

Các trường sau phải đồng bộ với `curated_molecules.json`:

```text
formula
charge
curated_molecule_id
```

Ví dụ:

```json
{
  "formula": "NH3",
  "charge": 0,
  "curated_molecule_id": "nh3",
  "cas_rn": "7664-41-7",
  "names": [
    "ammonia",
    "amoniac"
  ]
}
```

---

## 4. `curated_properties.json`

Đường dẫn:

```text
backend/app/data/curated_properties.json
```

Thêm dữ liệu vào object `properties` ở cấp cao nhất.

Khóa của mỗi loài hóa học có dạng:

```text
<formula>|<charge>
```

Ví dụ:

```text
H2O|0
NH3|0
NH4+|1
NO3-|-1
CO3^2-|-2
```

Tệp này dùng cho các tính chất riêng của phân tử đã được kiểm duyệt, chẳng hạn:

- trạng thái vật lý
- ngoại quan
- mùi
- nhiệt độ nóng chảy
- nhiệt độ sôi
- khối lượng riêng
- áp suất hơi
- moment lưỡng cực
- độ tan
- các tính chất vật lý/hóa học khác

### Mẫu

```json
"XY2|0": [
  {
    "key": "physical_state",
    "category": "physical",

    "label_vi": "Trạng thái vật lý",
    "label_en": "Physical state",

    "value": "Gas",
    "value_vi": "Khí",
    "value_en": "Gas",

    "evidence_type": "experimental",

    "source_name": "Tên nguồn",
    "source_reference": "Tài liệu tham khảo",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  },

  {
    "key": "boiling_point",
    "category": "physical",

    "label_vi": "Nhiệt độ sôi",
    "label_en": "Boiling point",

    "value": -10.0,
    "unit": "°C",

    "conditions": {
      "pressure": "760 mmHg"
    },

    "evidence_type": "experimental",

    "source_name": "Tên nguồn",
    "source_reference": "Tài liệu tham khảo",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  },

  {
    "key": "dipole_moment",
    "category": "chemical",

    "label_vi": "Moment lưỡng cực",
    "label_en": "Dipole moment",

    "value": 1.00,
    "unit": "D",

    "evidence_type": "experimental",

    "source_name": "Tên nguồn",
    "source_reference": "Tài liệu tham khảo",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  }
]
```

### Phân loại tính chất

Sử dụng một trong các nhóm chuẩn của mô hình dữ liệu hiện tại:

```text
identity
structural
physical
chemical
```

### Loại bằng chứng

Sử dụng loại nguồn phù hợp, ví dụ:

```text
experimental
source_annotation
computed
curated
deterministic
```

Không đánh dấu dữ liệu tính toán hoặc dữ liệu mô tả là `experimental`.

### Điều kiện đo

Giữ lại điều kiện đo khi có liên quan:

```json
"conditions": {
  "temperature": "25 °C",
  "pressure": "760 mmHg"
}
```

Nên giữ:

```text
tên nguồn
tài liệu tham khảo
URL
đơn vị
ngày truy xuất
điều kiện đo
```

khi các thông tin này có sẵn.

### Ion

Cần thận trọng với các tính chất vật lý khối của ion phân tử riêng lẻ.

Không nên lấy nhiệt độ nóng chảy, nhiệt độ sôi, khối lượng riêng hoặc các tính chất tương tự của một muối hay dung dịch rồi gán cho ion cô lập.

---

## 5. Đồng bộ dữ liệu giữa các tệp

Với cùng một phân tử, thông tin định danh phải thống nhất giữa các tệp.

Ví dụ với `NF3`:

### `curated_molecules.json`

```json
{
  "id": "nf3",
  "formula": "NF3",
  "charge": 0
}
```

### `chemical_identities.json`

```json
{
  "formula": "NF3",
  "charge": 0,
  "curated_molecule_id": "nf3"
}
```

### `experimental_geometries.json`

```json
"identity": {
  "formula": "NF3",
  "charge": 0,
  "curated_molecule_id": "nf3"
}
```

### `curated_properties.json`

```json
"NF3|0": [
  ...
]
```

Các trường quan trọng nhất cần đồng bộ là:

```text
formula
charge
curated molecule ID
atom inventory
CAS RN
PubChem CID
```

---

## 6. Mức dữ liệu tối thiểu được khuyến nghị

Với một phân tử mới, trước tiên nên hoàn thiện `curated_molecules.json` với:

```text
công thức và điện tích
tên chất
thành phần nguyên tử
nguyên tử trung tâm
công thức Lewis
điện tích hình thức
cộng hưởng
AXnEm
hình học miền electron
hình học phân tử
góc tham khảo riêng cho phân tử
độ phân cực
ghi chú giảng dạy
```

Sau đó bổ sung:

```text
experimental_geometries.json
```

khi có số liệu đáng tin cậy về:

```text
độ dài liên kết
góc liên kết
tọa độ thực nghiệm
```

Bổ sung:

```text
chemical_identities.json
```

để có:

```text
CAS RN
tên tìm kiếm
tên đồng nghĩa
```

Và bổ sung:

```text
curated_properties.json
```

khi có các tính chất đáng tin cậy cùng nguồn tham khảo rõ ràng.

---

## 7. Kiểm tra sau khi chỉnh sửa

Từ thư mục backend:

```bash
cd backend
pytest -q tests/test_catalog_integrity.py
```

Đây là bài kiểm tra quan trọng nhất sau khi thay đổi dữ liệu phân tử.

Ngoài ra nên chạy:

```bash
pytest -q tests/test_golden_pipeline.py
pytest -q tests/test_reference_bond_angle.py
pytest -q tests/test_geometry_evidence.py
pytest -q tests/test_properties.py
```

Để kiểm tra toàn bộ backend:

```bash
pytest -q
```

---

## 8. Danh sách kiểm tra cuối

Trước khi commit một phân tử đã được bổ sung dữ liệu, hãy kiểm tra:

- [ ] Công thức đúng.
- [ ] Điện tích đúng.
- [ ] ID phân tử là duy nhất.
- [ ] Thành phần nguyên tử khớp với công thức.
- [ ] Nguyên tử trung tâm nằm đầu tiên trong `atom_symbols`.
- [ ] Bậc liên kết Lewis đúng.
- [ ] Số cặp electron tự do đúng.
- [ ] Điện tích hình thức đúng và tổng bằng điện tích toàn phân tử/ion.
- [ ] Tổng số electron hóa trị đúng.
- [ ] Thông tin cộng hưởng đúng.
- [ ] Số miền electron VSEPR đúng.
- [ ] AXnEm đúng.
- [ ] Hình học miền electron đúng.
- [ ] Hình học phân tử đúng.
- [ ] Góc riêng của phân tử đúng.
- [ ] Độ dài/góc thực nghiệm có nguồn rõ ràng.
- [ ] Các góc không tương đương được giữ tách biệt.
- [ ] Số CAS và các định danh ngoài đã được xác minh.
- [ ] Tính chất giữ nguyên đơn vị và điều kiện đo.
- [ ] Các tính chất có nguồn tham khảo.
- [ ] Thông tin định danh đồng bộ giữa các tệp.
- [ ] `pytest -q tests/test_catalog_integrity.py` chạy thành công.
- [ ] Toàn bộ test backend chạy thành công trước khi merge.

---

## Tóm tắt các tệp được khuyến nghị

Đối với việc bổ sung dữ liệu phân tử trực tiếp bằng mã nguồn, nên tập trung vào:

```text
backend/app/data/curated_molecules.json
backend/app/data/experimental_geometries.json
backend/app/data/chemical_identities.json
backend/app/data/curated_properties.json
```

Bốn tệp này tương ứng với:

```text
Dữ liệu Lewis/VSEPR cốt lõi
+ hình học thực nghiệm
+ thông tin định danh phục vụ tìm kiếm
+ tính chất vật lý/hóa học đã kiểm duyệt
```
