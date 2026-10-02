| Đối tượng | Guest | Customer | Staff | Manager | Security | Operations | Super |
|---|---|---|---|---|---|---|---|
| Public books | R | R | R | CRUD | R | R | CRUD |
| Authors | R | R | R | CRUD | R | R | CRUD |
| Categories | R | R | R | CRUD | R | R | CRUD |
| Publishers | R | R | R | CRUD | R | R | CRUD |
| Suppliers | - | - | - | CRUD | - | R giới hạn | CRUD |
| Images | R | R | R | CRUD | R | R | CRUD |
| Own profile | - | RU | RU | RU | RU | RU | RU |
| Other users | - | - | - | Staff basic | R security | - | CRUD |
| Cart | - | CRUD own | - | - | - | - | CRUD |
| Orders | - | CR own | RU workflow | RU | R khi cần | R thống kê | CRUD |
| Order items | - | R own | R | R | R khi điều tra | R thống kê | CRUD |
| Payments | - | R own | R status | R status | R khi điều tra | R thống kê | CRUD kiểm soát |
| Inventory | - | - | R tối thiểu | CRUD qua nghiệp vụ | - | R | CRUD |
| Reviews | R | CRU own + R others | R | R/moderate | R | - | CRUD |
| Sessions | - | R/revoke own | own | own | R/revoke | own | CRUD |
| Login attempts | - | - | - | - | R | R thống kê | R |
| Audit logs | - | - | - | - | R | R vận hành | R |
| Security events | - | - | - | - | RU resolution | R | CRUD có giới hạn |
| Roles | - | - | - | Staff only | non-admin roles | - | CRUD |
| Backup | - | - | - | - | R metadata | CR/restore | CRUD |
C = Create
R = Read
U = Update
D = Delete