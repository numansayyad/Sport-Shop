# User Profile & Rewards System TODO

**Approved Plan**:
1. Add score=0 to users.insert_one in routes/auth.py register()
2. Edit templates/base.html navbar: Welcome message + Profile link
3. Create routes/profile.py blueprint with /profile route
4. Create templates/profile.html with stats, rewards, activity
5. Edit routes/orders.py: Add points calculation after order (10/product + 5/₹100)
6. Add helper functions for name formatting, reward levels

**Steps**:
- [ ] 1. Edit auth.py register - add "score": 0
- [ ] 2. Edit base.html navbar
- [ ] 3. Create routes/profile.py
- [ ] 4. Create templates/profile.html
- [ ] 5. Edit orders.py add points logic
- [ ] 6. Edit app.py register profile_bp
- [ ] 7. Test

**Status**: Starting...

