import os
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

class SourdoughPlanner:
    def __init__(self, starter_amount, start_time, hydration=70, flour_type="bread flour"):
        self.starter_amount = starter_amount
        self.start_time = start_time
        self.hydration = hydration
        self.flour_type = flour_type
        self.schedule = []
        
    def calculate_ingredients(self):
        # Starter feeding ratios (1:5:5 - starter:flour:water)
        feeding_flour = self.starter_amount * 5
        feeding_water = self.starter_amount * 5
        
        # Main dough ratios (1:5:3.5:0.1 - starter:flour:water:salt)
        total_flour = self.starter_amount * 5
        total_water = (total_flour * self.hydration) / 100
        salt = total_flour * 0.02  # 2% of flour weight
        
        return {
            'feeding': {
                'existing_starter': self.starter_amount,
                'flour': feeding_flour,
                'water': feeding_water
            },
            'dough': {
                'fed_starter': self.starter_amount * 11,  # After feeding
                'flour': total_flour,
                'water': total_water,
                'salt': salt
            }
        }
    
    def generate_schedule(self):
        ingredients = self.calculate_ingredients()
        
        # Parse start time
        start_dt = datetime.strptime(self.start_time, "%I:%M %p")
        base_date = datetime.now().replace(hour=start_dt.hour, minute=start_dt.minute, second=0, microsecond=0)
        
        # Day 1 - Starter preparation
        day1_morning = base_date
        day1_evening = day1_morning + timedelta(hours=12)
        
        # Day 2 - Dough preparation and baking
        day2_morning = day1_morning + timedelta(days=1)
        day2_autolyse = day2_morning + timedelta(hours=1)
        day2_mix = day2_morning + timedelta(hours=1, minutes=30)
        day2_bulk_start = day2_morning + timedelta(hours=2)
        day2_fold1 = day2_bulk_start + timedelta(minutes=30)
        day2_fold2 = day2_bulk_start + timedelta(hours=1)
        day2_fold3 = day2_bulk_start + timedelta(hours=1, minutes=30)
        day2_bulk_end = day2_bulk_start + timedelta(hours=4)
        day2_shape = day2_bulk_end
        day2_final_proof = day2_shape + timedelta(minutes=30)
        day2_bake = day2_final_proof + timedelta(hours=2)
        
        self.schedule = [
            {
                'day': 'Day 1',
                'time': day1_morning.strftime("%I:%M %p"),
                'task': 'Feed Starter',
                'details': f'Mix {ingredients["feeding"]["existing_starter"]}g existing starter + {ingredients["feeding"]["flour"]}g {self.flour_type} + {ingredients["feeding"]["water"]}g water',
                'notes': 'Let starter double in size (6-12 hours)'
            },
            {
                'day': 'Day 1',
                'time': day1_evening.strftime("%I:%M %p"),
                'task': 'Check Starter',
                'details': 'Starter should be doubled and bubbly',
                'notes': 'If not ready, wait longer or feed again'
            },
            {
                'day': 'Day 2',
                'time': day2_morning.strftime("%I:%M %p"),
                'task': 'Float Test',
                'details': 'Drop small amount of starter in water - should float',
                'notes': 'If sinks, starter needs more time'
            },
            {
                'day': 'Day 2',
                'time': day2_autolyse.strftime("%I:%M %p"),
                'task': 'Autolyse',
                'details': f'Mix {ingredients["dough"]["flour"]}g flour + {ingredients["dough"]["water"]}g water only',
                'notes': 'No starter or salt yet. Cover and rest 30 minutes'
            },
            {
                'day': 'Day 2',
                'time': day2_mix.strftime("%I:%M %p"),
                'task': 'Final Mix',
                'details': f'Add {self.starter_amount * 11}g active starter + {ingredients["dough"]["salt"]}g salt',
                'notes': 'Mix by hand until well combined'
            },
            {
                'day': 'Day 2',
                'time': day2_bulk_start.strftime("%I:%M %p"),
                'task': 'Bulk Fermentation Begins',
                'details': 'Cover dough and start bulk fermentation',
                'notes': 'Dough should increase by 50-70%'
            },
            {
                'day': 'Day 2',
                'time': day2_fold1.strftime("%I:%M %p"),
                'task': 'First Fold',
                'details': 'Perform set of stretch and folds',
                'notes': '4 folds: North, South, East, West'
            },
            {
                'day': 'Day 2',
                'time': day2_fold2.strftime("%I:%M %p"),
                'task': 'Second Fold',
                'details': 'Perform set of stretch and folds',
                'notes': 'Dough should feel stronger'
            },
            {
                'day': 'Day 2',
                'time': day2_fold3.strftime("%I:%M %p"),
                'task': 'Third Fold',
                'details': 'Perform final set of stretch and folds',
                'notes': 'Last folds - let dough rest undisturbed after this'
            },
            {
                'day': 'Day 2',
                'time': day2_bulk_end.strftime("%I:%M %p"),
                'task': 'End Bulk Fermentation',
                'details': 'Check if dough has increased by 50-70%',
                'notes': 'Should be jiggly and have visible air bubbles'
            },
            {
                'day': 'Day 2',
                'time': day2_shape.strftime("%I:%M %p"),
                'task': 'Pre-shape',
                'details': 'Turn out dough and pre-shape into round',
                'notes': 'Rest 20-30 minutes before final shaping'
            },
            {
                'day': 'Day 2',
                'time': day2_final_proof.strftime("%I:%M %p"),
                'task': 'Final Shape & Proof',
                'details': 'Shape into boule or batard, place in banneton',
                'notes': 'Proof 1.5-2 hours at room temp or overnight in fridge'
            },
            {
                'day': 'Day 2',
                'time': day2_bake.strftime("%I:%M %p"),
                'task': 'Preheat & Bake',
                'details': 'Preheat Dutch oven to 450°F (230°C)',
                'notes': 'Score, bake covered 20 min, uncovered 20-25 min'
            }
        ]
        
        return self.schedule

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_schedule():
    try:
        data = request.get_json()
        
        starter_amount = int(data.get('starter_amount', 100))
        start_time = data.get('start_time', '8:00 AM')
        hydration = int(data.get('hydration', 70))
        flour_type = data.get('flour_type', 'bread flour')
        custom_notes = data.get('custom_notes', '')
        
        planner = SourdoughPlanner(starter_amount, start_time, hydration, flour_type)
        schedule = planner.generate_schedule()
        ingredients = planner.calculate_ingredients()
        
        return jsonify({
            'success': True,
            'schedule': schedule,
            'ingredients': ingredients,
            'custom_notes': custom_notes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

# CRITICAL: This configuration is needed for web deployment
if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
else:
    # For production deployment (Render, Heroku, etc.)
    # This ensures the app runs correctly when imported by gunicorn
    pass
