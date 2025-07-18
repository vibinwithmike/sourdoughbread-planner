# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

class SourdoughPlanner:
    def __init__(self):
        self.starter_flour_ratio = 5
        self.starter_water_ratio = 5
        self.main_flour_ratio = 5
        self.main_water_ratio = 3.5
        self.salt_ratio = 0.1
        
    def parse_time(self, time_str):
        """Parse time string in 12-hour format"""
        try:
            time_str = time_str.strip().upper()
            
            if not ('AM' in time_str or 'PM' in time_str):
                hour = int(time_str.split(':')[0])
                if 6 <= hour <= 11:
                    time_str += ' AM'
                else:
                    time_str += ' PM'
            
            return datetime.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            try:
                return datetime.strptime(time_str, '%I %p').time()
            except ValueError:
                raise ValueError(f"Invalid time format: {time_str}")
    
    def format_time(self, dt):
        """Format datetime to 12-hour format"""
        return dt.strftime('%I:%M %p').lstrip('0')
    
    def format_date_time(self, dt):
        """Format datetime with date and time"""
        return dt.strftime('%A, %B %d - %I:%M %p').replace(' 0', ' ')
    
    def calculate_ingredients(self, starter_amount, hydration=70):
        """Calculate all ingredient amounts"""
        starter_flour = starter_amount * self.starter_flour_ratio
        starter_water = starter_amount * self.starter_water_ratio
        total_starter_after_feeding = starter_amount + starter_flour + starter_water
        
        main_flour = starter_amount * self.main_flour_ratio
        main_water = starter_amount * self.main_water_ratio
        
        if hydration != 70:
            standard_hydration = (main_water / main_flour) * 100
            adjustment_factor = hydration / standard_hydration
            main_water = main_water * adjustment_factor
        
        salt = starter_amount * self.salt_ratio
        
        return {
            'starter_amount': starter_amount,
            'starter_flour': starter_flour,
            'starter_water': starter_water,
            'total_starter_after_feeding': total_starter_after_feeding,
            'main_flour': main_flour,
            'main_water': main_water,
            'salt': salt,
            'total_flour': starter_flour + main_flour,
            'total_water': starter_water + main_water,
            'final_hydration': round(((starter_water + main_water) / (starter_flour + main_flour)) * 100, 1)
        }
    
    def calculate_timeline(self, start_time_str, start_date=None):
        """Calculate complete timeline"""
        if start_date is None:
            start_date = datetime.now().date()
        
        start_time = self.parse_time(start_time_str)
        start_datetime = datetime.combine(start_date, start_time)
        
        timeline = {}
        timeline['feed_starter'] = start_datetime
        timeline['peak'] = start_datetime + timedelta(hours=12)
        timeline['autolyse'] = timeline['peak']
        timeline['fold_1'] = timeline['peak'] + timedelta(minutes=30)
        timeline['fold_2'] = timeline['peak'] + timedelta(hours=1)
        timeline['fold_3'] = timeline['peak'] + timedelta(hours=1, minutes=30)
        timeline['fold_4'] = timeline['peak'] + timedelta(hours=2)
        timeline['bulk_fermentation'] = timeline['fold_4']
        timeline['pre_shape'] = timeline['bulk_fermentation'] + timedelta(hours=12)
        timeline['final_shape'] = timeline['pre_shape'] + timedelta(minutes=30)
        timeline['cold_proof'] = timeline['final_shape'] + timedelta(minutes=30)
        timeline['preheat'] = timeline['cold_proof'] + timedelta(hours=8)
        timeline['bake'] = timeline['preheat'] + timedelta(minutes=30)
        timeline['cool'] = timeline['bake'] + timedelta(minutes=45)
        
        return timeline
    
    def generate_schedule_data(self, starter_amount, start_time_str, hydration=70, flour_type="bread flour", notes=None):
        """Generate schedule data for web display"""
        ingredients = self.calculate_ingredients(starter_amount, hydration)
        timeline = self.calculate_timeline(start_time_str)
        
        # Group timeline by days
        days = {}
        for step, dt in timeline.items():
            date_key = dt.date()
            if date_key not in days:
                days[date_key] = []
            days[date_key].append((step, dt))
        
        # Sort days and steps
        sorted_days = []
        for date_key in sorted(days.keys()):
            day_steps = sorted(days[date_key], key=lambda x: x[1])
            sorted_days.append((date_key, day_steps))
        
        return {
            'ingredients': ingredients,
            'timeline': timeline,
            'days': sorted_days,
            'flour_type': flour_type,
            'notes': notes
        }

# Initialize planner
planner = SourdoughPlanner()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_schedule():
    try:
        data = request.json
        starter_amount = float(data.get('starter_amount', 100))
        start_time = data.get('start_time', '8:00 AM')
        hydration = int(data.get('hydration', 70))
        flour_type = data.get('flour_type', 'bread flour')
        notes = data.get('notes', '')
        
        schedule_data = planner.generate_schedule_data(
            starter_amount, start_time, hydration, flour_type, notes
        )
        
        # Format data for JSON response
        formatted_data = {
            'success': True,
            'ingredients': schedule_data['ingredients'],
            'timeline': {k: v.isoformat() for k, v in schedule_data['timeline'].items()},
            'days': [
                {
                    'date': date.strftime('%A, %B %d'),
                    'steps': [
                        {
                            'step': step,
                            'time': dt.strftime('%I:%M %p').lstrip('0'),
                            'datetime': dt.isoformat()
                        }
                        for step, dt in day_steps
                    ]
                }
                for date, day_steps in schedule_data['days']
            ],
            'flour_type': flour_type,
            'notes': notes
        }
        
        return jsonify(formatted_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
