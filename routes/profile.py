from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import os
from extensions import mongo
from bson import ObjectId
from datetime import datetime

profile_bp = Blueprint('profile_bp', __name__, url_prefix='/profile')

@profile_bp.route('/', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please login first!', 'warning')
        return redirect(url_for('auth_bp.login'))
    
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        flash('User not found!')
        return redirect(url_for('auth_bp.logout'))
    
    if request.method == 'POST':
        # Edit profile
        new_name = request.form.get('name', user['username']).strip()
        new_age = request.form.get('age', '').strip()
        new_dob = request.form.get('dob', '').strip()
        profile_pic = request.files.get('profile_pic')
        
        update_data = {
            'username': new_name,
            'age': int(new_age) if new_age else None,
            'dob': new_dob
        }
        
        if profile_pic and profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            if filename:
                filename = f"profiles_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                filepath = os.path.join(current_app.root_path, 'static/uploads/profiles', filename)
                profile_pic.save(filepath)
                update_data['profile_pic'] = f"uploads/profiles/{filename}"
        
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
        flash('Profile updated successfully!')
        return redirect(url_for('profile_bp.profile'))
    
    # Recent orders
    recent_orders = list(mongo.db.orders.find({'user_id': ObjectId(user_id)}).sort('ordered_at', -1).limit(5))
    
    # Reward info
    score = user.get('score', 0)
    
    # Calculate reward level
    if score >= 5000:
        level = '🏆 Platinum'
        progress = 100
    elif score >= 2500:
        level = '🥈 Gold'
        progress = (score - 0) / 2500 * 100
    elif score >= 1000:
        level = '🥈 Silver'
        progress = (score - 0) / 1000 * 100
    else:
        level = '🥉 Beginner'
        progress = (score / 1000) * 100
    
    # Points needed for next level
    next_level_points = 1000 if score < 1000 else 2500 if score < 2500 else 5000
    
    return render_template('profile.html', user=user, recent_orders=recent_orders, score=score, level=level, progress=progress, next_level_points=next_level_points)
