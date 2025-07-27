# app.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os

# Create Flask app
app = Flask(__name__)

class SourdoughPlanner:
    def __init__(self):
        # Define feeding ratios and their characteristics
        self.feeding_ratios = {
            '1:1:1': {
                'starter_parts': 1,
                'flour_parts': 1,
                'water_parts': 1,
                'peak_hours': 5,
                'description': 'Fast (4-6 hours) - Same day baking'
            },
            '1:2:2': {
                'starter_parts': 1,
                'flour_parts': 2,
                'water_parts': 2,
                'peak_hours': 7,
                'description': 'Moderate (6-8 hours) - Balanced timing'
            },
            '1:3:3': {
                'starter_parts': 1,
                'flour_parts': 3,
                'water_parts': 3,
                'peak_hours': 9,
                'description': 'Standard (8-10 hours) - Daily maintenance'
            },
            '1:4:4': {
                'starter_parts': 1,
                'flour_parts': 4,
                'water_parts': 4,
                'peak_hours': 11,
                'description': 'Professional (10-12 hours) - Most common'
            },
            '1:5:5': {
                'starter_parts': 1,
                'flour_parts': 5,
                'water_parts': 5,
                'peak_hours': 12,
                'description': 'Overnight (12-14 hours) - Work schedule'
            },
            '1:10:10': {
                'starter_parts': 1,
                'flour_parts': 10,
                'water_parts': 10,
                'peak_hours': 20,
                'description': 'Extended (16-24 hours) - Weekend baking'
            }
        }
        
        # Standard recipe ratios (based on active starter amount)
        self.standard_active_starter = 120  # Base amount for recipe calculations
        self.main_flour_ratio = 50/12  # Additional flour ratio
        self.main_water_ratio = 35/12  # Additional water ratio  
        self.salt_ratio = 1/12         # Salt ratio

    def get_feeding_ratios(self):
        """Return available feeding ratios for frontend"""
        return {k: v['description'] for k, v in self.feeding_ratios.items()}

    def calculate_feeding_from_existing(self, existing_starter_amount, feeding_ratio):
        """Calculate feeding amounts starting from existing starter amount"""
        ratio_info = self.feeding_ratios[feeding_ratio]
        
        # Use existing starter amount as the starter portion
        starter_used = existing_starter_amount
        flour_needed = existing_starter_amount * ratio_info['flour_parts']
        water_needed = existing_starter_amount * ratio_info['water_parts']
        
        # Calculate total after feeding
        total_after_feeding = starter_used + flour_needed + water_needed
        
        return {
            'existing_starter_used': round(starter_used, 1),
            'flour_to_add': round(flour_needed, 1),
            'water_to_add': round(water_needed, 1),
            'total_after_feeding': round(total_after_feeding, 1),
            'peak_hours': ratio_info['peak_hours']
        }

    def calculate_ingredients(self, existing_starter_amount, feeding_ratio, hydration=70):
        """Calculate all ingredient amounts based on existing starter amount and feeding ratio"""
        # Calculate starter feeding
        starter_feeding = self.calculate_feeding_from_existing(existing_starter_amount, feeding_ratio)
        active_starter_amount = starter_feeding['total_after_feeding']
        
        # Use ALL the active starter in the bread recipe
        starter_for_bread = active_starter_amount
        
        # Calculate main dough ingredients based on all active starter
        main_flour = starter_for_bread * self.main_flour_ratio
        main_water = starter_for_bread * self.main_water_ratio
        
        # Adjust water for different hydration levels
        if hydration != 70:
            # Calculate current hydration and adjust
            total_flour = starter_feeding['flour_to_add'] + main_flour
            current_water = starter_feeding['water_to_add'] + main_water
            current_hydration = (current_water / total_flour) * 100
            
            # Adjust main water to achieve target hydration
            target_water = (total_flour * hydration) / 100
            water_adjustment = target_water - current_water
            main_water += water_adjustment
        
        salt = starter_for_bread * self.salt_ratio
        
        total_flour = starter_feeding['flour_to_add'] + main_flour
        total_water = starter_feeding['water_to_add'] + main_water
        
        return {
            'feeding_ratio': feeding_ratio,
            'starter_feeding': starter_feeding,
            'active_starter_amount': round(active_starter_amount, 1),
            'starter_for_bread': round(starter_for_bread, 1),
            'main_flour': round(main_flour, 1),
            'main_water': round(main_water, 1),
            'salt': round(salt, 1),
            'total_flour': round(total_flour, 1),
            'total_water': round(total_water, 1),
            'final_hydration': round((total_water / total_flour) * 100, 1)
        }

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

    def calculate_timeline(self, start_time_str, feeding_ratio, start_date=None):
        """Calculate complete timeline based on feeding ratio"""
        if start_date is None:
            start_date = datetime.now().date()
        
        start_time = self.parse_time(start_time_str)
        start_datetime = datetime.combine(start_date, start_time)
        
        # Get peak time based on feeding ratio
        peak_hours = self.feeding_ratios[feeding_ratio]['peak_hours']
        
        timeline = {}
        timeline['feed_starter'] = start_datetime
        timeline['peak_ready'] = start_datetime + timedelta(hours=peak_hours)
        timeline['mix_dough'] = timeline['peak_ready']
        timeline['autolyse_end'] = timeline['mix_dough'] + timedelta(minutes=30)
        timeline['fold_1'] = timeline['autolyse_end']
        timeline['fold_2'] = timeline['fold_1'] + timedelta(minutes=30)
        timeline['fold_3'] = timeline['fold_2'] + timedelta(minutes=30)
        timeline['fold_4'] = timeline['fold_3'] + timedelta(minutes=30)
        timeline['bulk_fermentation_start'] = timeline['fold_4']
        
        # Bulk fermentation timing varies by temperature and starter amount
        # For overnight method, typically 8-12 hours
        bulk_hours = 10  # Default, could be made adjustable
        timeline['bulk_fermentation_end'] = timeline['bulk_fermentation_start'] + timedelta(hours=bulk_hours)
        
        timeline['pre_shape'] = timeline['bulk_fermentation_end']
        timeline['bench_rest_end'] = timeline['pre_shape'] + timedelta(minutes=30)
        timeline['final_shape'] = timeline['bench_rest_end']
        timeline['cold_proof_start'] = timeline['final_shape']
        
        # Cold proof for 8+ hours
        timeline['ready_to_bake'] = timeline['cold_proof_start'] + timedelta(hours=8)
        timeline['preheat_oven'] = timeline['ready_to_bake']
        timeline['bake'] = timeline['preheat_oven'] + timedelta(minutes=30)
        timeline['cooling_done'] = timeline['bake'] + timedelta(hours=2)
        
        return timeline

    def generate_schedule_data(self, existing_starter_amount, start_time_str, feeding_ratio='1:5:5', 
                             hydration=70, flour_type="bread flour", notes=None):
        """Generate schedule data for web display"""
        ingredients = self.calculate_ingredients(existing_starter_amount, feeding_ratio, hydration)
        timeline = self.calculate_timeline(start_time_str, feeding_ratio)
        
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
            'notes': notes,
            'feeding_ratio': feeding_ratio
        }

# Helper functions for formatting
def format_step_name(step):
    """Format step names for display"""
    step_names = {
        'feed_starter': 'Feed Starter',
        'peak_ready': 'Starter at Peak',
        'mix_dough': 'Mix Dough',
        'autolyse_end': 'End Autolyse',
        'fold_1': 'Stretch & Fold #1',
        'fold_2': 'Stretch & Fold #2', 
        'fold_3': 'Stretch & Fold #3',
        'fold_4': 'Stretch & Fold #4',
        'bulk_fermentation_start': 'Begin Bulk Fermentation',
        'bulk_fermentation_end': 'End Bulk Fermentation',
        'pre_shape': 'Pre-shape Dough',
        'bench_rest_end': 'End Bench Rest',
        'final_shape': 'Final Shape',
        'cold_proof_start': 'Start Cold Proof',
        'ready_to_bake': 'Ready to Bake',
        'preheat_oven': 'Preheat Oven',
        'bake': 'Bake Bread',
        'cooling_done': 'Cooling Complete'
    }
    return step_names.get(step, step.replace('_', ' ').title())

def get_step_description(step):
    """Get description for each step"""
    descriptions = {
        'feed_starter': 'Add flour and water to your existing starter',
        'peak_ready': 'Starter should be bubbly and at peak activity',
        'mix_dough': 'Mix water, active starter, salt, then add flour',
        'autolyse_end': 'Let mixed dough rest covered',
        'fold_1': 'First set of stretch and folds',
        'fold_2': 'Second set of stretch and folds',
        'fold_3': 'Third set of stretch and folds', 
        'fold_4': 'Final set of stretch and folds',
        'bulk_fermentation_start': 'Cover and let ferment overnight',
        'bulk_fermentation_end': 'Dough should be doubled or more',
        'pre_shape': 'Shape into loose ball, let rest',
        'bench_rest_end': 'Dough has relaxed and spread slightly',
        'final_shape': 'Shape into final form and place in banneton',
        'cold_proof_start': 'Place in fridge for cold retard',
        'ready_to_bake': 'Remove from fridge, preheat Dutch oven',
        'preheat_oven': 'Heat oven and Dutch oven to 450°F',
        'bake': 'Score and bake: 30 min covered, 15 min uncovered',
        'cooling_done': 'Bread is cool enough to slice'
    }
    return descriptions.get(step, '')

# Routes
@app.route('/')
def index():
    try:
        planner = SourdoughPlanner()
        feeding_ratios = planner.get_feeding_ratios()
        current_time = get_current_time_12hr()
        return render_template('index.html', feeding_ratios=feeding_ratios, current_time=current_time)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/test')
def test_route():
    return "Flask is working! This is a test route."

@app.route('/debug')
def debug():
    import os
    return jsonify({
        'current_directory': os.getcwd(),
        'files_in_root': os.listdir('.'),
        'templates_exists': os.path.exists('templates'),
        'index_exists': os.path.exists('templates/index.html'),
        'flask_working': True
    })

@app.route('/generate', methods=['POST'])
def generate_schedule():
    try:
        planner = SourdoughPlanner()
        data = request.json
        existing_starter_amount = float(data.get('existing_starter_amount', 50))
        start_time = data.get('start_time', '8:00 AM')
        feeding_ratio = data.get('feeding_ratio', '1:5:5')
        hydration = int(data.get('hydration', 70))
        flour_type = data.get('flour_type', 'bread flour')
        notes = data.get('notes', '')
        
        # Validate feeding ratio
        if feeding_ratio not in planner.feeding_ratios:
            return jsonify({'success': False, 'error': 'Invalid feeding ratio'}), 400
        
        schedule_data = planner.generate_schedule_data(
            existing_starter_amount, start_time, feeding_ratio, hydration, flour_type, notes
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
                            'step': format_step_name(step),
                            'time': dt.strftime('%I:%M %p').lstrip('0'),
                            'datetime': dt.isoformat(),
                            'description': get_step_description(step)
                        }
                        for step, dt in day_steps
                    ]
                }
                for date, day_steps in schedule_data['days']
            ],
            'flour_type': flour_type,
            'notes': notes,
            'feeding_ratio': feeding_ratio,
            'feeding_ratio_info': planner.feeding_ratios[feeding_ratio]
        }
        
        return jsonify(formatted_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/ratios')
def get_ratios():
    try:
        planner = SourdoughPlanner()
        return jsonify(planner.get_feeding_ratios())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# CRITICAL: This is what gunicorn looks for
if __name__ == '__main__':
    # Use PORT environment variable provided by Render
    port = int(os.environ.get('PORT', 10000))
    # IMPORTANT: Bind to 0.0.0.0, not localhost
    app.run(host='0.0.0.0', port=port, debug=False)
