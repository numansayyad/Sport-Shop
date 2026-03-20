# Fix Stock Display & Decrease - Updated TODO

## Plan:
Remove `setdefault("stock", 0)` overwrites from routes/products.py

## Steps:\n- [x] 1. Update TODO.md\n- [x] 2. Edit routes/products.py: remove product_details setdefault stock\n- [x] 3. Edit routes/products.py: remove list_products loop setdefault\n- [x] 4. Edit routes/products.py: remove admin_products loop setdefault\n- [ ] 5. Restart app\n- [ ] 6. Test: admin set stock=5 → pages show 5 → buy → decreases\n\n**Status:** Code fixes complete! ✅\n**Changes:** Removed stock-overwriting setdefault from 3 locations.
