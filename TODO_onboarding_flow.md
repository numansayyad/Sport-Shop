# TODO: First-Time User Onboarding Flow
1. [x] Add /onboarding route to routes/profile.py (multi-step: pic -> details)
2. [x] Update auth.py login: check incomplete profile → session['needs_onboarding'] = True → /onboarding
3. [x] Create templates/onboarding_step1.html (pic upload/set/skip)
4. [x] Create templates/onboarding_step2.html (age/dob/save/skip)
5. [x] Update templates/profile.html: remove edit form, add "Complete Profile" link if incomplete
6. [ ] Test: register → login → onboarding → main site; edit profile → no onboarding
7. [ ] Complete task


