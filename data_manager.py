import json
import os
from datetime import datetime

DATA_FILE = "data/user_data.json"
BACKUP_DIR = "data/backups"

def ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

def load_data():
    ensure_data_dir()
        
    if not os.path.exists(DATA_FILE):
        default_data = {
            "balance": 0,
            "expenses": [],
            "budget": {},
            "goals": [],
            "investments": [],
            "income": [],
            "settings": {
                "currency": "Rp",
                "theme": "light",
                "monthly_budget_limit": 0
            }
        }
        save_data(default_data)
        return default_data
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    
    defaults = {
        "balance": 0, "expenses": [], "budget": {}, 
        "goals": [], "investments": [], "income": []
    }
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
            
    return data

def save_data(data):
    ensure_data_dir()
    
    backup_files = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('backup_')])
    if len(backup_files) >= 5:
        os.remove(os.path.join(BACKUP_DIR, backup_files[0]))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}.json")
    
    with open(backup_path, 'w') as f:
        json.dump(data, f, indent=4)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_expenses_by_category(data, year=None, month=None):
    expenses = data.get('expenses', [])
    category_totals = {}
    
    for exp in expenses:
        if year and month:
            if 'date' not in exp: continue
            try:
                exp_date = datetime.strptime(exp['date'], '%Y-%m-%d')
                if exp_date.year != year or exp_date.month != month:
                    continue
            except: continue
            
        cat = exp.get('category', 'Lainnya')
        amount = exp.get('amount', 0)
        category_totals[cat] = category_totals.get(cat, 0) + amount
    
    return category_totals

def get_income_by_category(data):
    income = data.get('income', [])
    category_totals = {}
    
    for inc in income:
        cat = inc.get('category', 'Lainnya')
        amount = inc.get('amount', 0)
        category_totals[cat] = category_totals.get(cat, 0) + amount
    
    return category_totals

def get_monthly_summary(data, year=None, month=None):
    if year is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    expenses = data.get('expenses', [])
    income = data.get('income', [])
    
    monthly_expenses = []
    monthly_income = []
    
    for exp in expenses:
        if 'date' in exp:
            exp_date = datetime.strptime(exp['date'], '%Y-%m-%d')
            if exp_date.year == year and exp_date.month == month:
                monthly_expenses.append(exp)
    
    for inc in income:
        if 'date' in inc:
            inc_date = datetime.strptime(inc['date'], '%Y-%m-%d')
            if inc_date.year == year and inc_date.month == month:
                monthly_income.append(inc)
    
    total_expenses = sum(e['amount'] for e in monthly_expenses)
    total_income = sum(i['amount'] for i in monthly_income)
    
    return {
        'expenses': monthly_expenses,
        'income': monthly_income,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'net_savings': total_income - total_expenses,
        'year': year,
        'month': month
    }

def get_historical_monthly_summaries(data, num_months=6):
    summaries = []
    current_date = datetime.now()
    for i in range(num_months):
        target_month = current_date.month - i
        target_year = current_date.year
        while target_month <= 0:
            target_month += 12
            target_year -= 1
        
        summary = get_monthly_summary(data, target_year, target_month)
        summaries.append({
            'month_year': datetime(target_year, target_month, 1).strftime('%Y-%m'),
            'net_savings': summary['net_savings'],
            'total_income': summary['total_income'],
            'total_expenses': summary['total_expenses']
        })
    return list(reversed(summaries))


def set_budget(data, category, amount):
    if 'budget' not in data:
        data['budget'] = {}
    data['budget'][category] = amount
    save_data(data)
    return data

def delete_expense(data, index):
    if 0 <= index < len(data.get('expenses', [])):
        removed = data['expenses'].pop(index)
        data['balance'] += removed.get('amount', 0)
        save_data(data)
    return data

def delete_income(data, index):
    if 0 <= index < len(data.get('income', [])):
        removed = data['income'].pop(index)
        data['balance'] -= removed.get('amount', 0)
        save_data(data)
    return data

def update_expense(data, index, updated_entry):
    if 0 <= index < len(data.get('expenses', [])):
        old_amount = data['expenses'][index].get('amount', 0)
        new_amount = updated_entry.get('amount', 0)
        data['expenses'][index] = updated_entry
        data['balance'] = data['balance'] + old_amount - new_amount
        save_data(data)
    return data

def update_income(data, index, updated_entry):
    if 0 <= index < len(data.get('income', [])):
        old_amount = data['income'][index].get('amount', 0)
        new_amount = updated_entry.get('amount', 0)
        data['income'][index] = updated_entry
        data['balance'] = data['balance'] - old_amount + new_amount
        save_data(data)
    return data

def delete_goal(data, goal_id):
    data['goals'] = [g for g in data.get('goals', []) if g.get('id') != goal_id]
    save_data(data)
    return data

def delete_investment(data, investment_id):
    data['investments'] = [i for i in data.get('investments', []) if i.get('id') != investment_id]
    save_data(data)
    return data

def get_budget_status(data):
    now = datetime.now()
    expenses_by_cat = get_expenses_by_category(data, now.year, now.month)
    budgets = data.get('budget', {})
    
    status = {}
    all_categories = set(list(expenses_by_cat.keys()) + list(budgets.keys()))
    
    for cat in all_categories:
        spent = expenses_by_cat.get(cat, 0)
        budgeted = budgets.get(cat, 0)
        remaining = budgeted - spent
        percent_used = (spent / budgeted * 100) if budgeted > 0 else 0
        
        status[cat] = {
            'budget': budgeted,
            'spent': spent,
            'remaining': remaining,
            'percent_used': percent_used
        }
    
    return status

def add_savings_goal(data, name, target_amount, deadline=None):
    if 'goals' not in data:
        data['goals'] = []
    
    new_goal = {
        'id': len(data['goals']) + 1,
        'name': name,
        'target_amount': target_amount,
        'current_amount': 0,
        'deadline': deadline,
        'created_date': datetime.now().strftime('%Y-%m-%d'),
        'status': 'active',
        'roi_percentage': 0.0
    }
    
    data['goals'].append(new_goal)
    save_data(data)
    return data

def update_savings_goal(data, goal_id, amount):
    for goal in data.get('goals', []):
        if goal.get('id') == goal_id:
            goal['current_amount'] = amount
            if amount >= goal['target_amount']:
                goal['status'] = 'completed'
            save_data(data)
            return data
    
    return data

def add_investment(data, name, amount, investment_type, purchase_date=None):
    if 'investments' not in data:
        data['investments'] = []
    
    new_investment = {
        'id': len(data['investments']) + 1,
        'name': name,
        'amount': amount,
        'type': investment_type,
        'purchase_date': purchase_date or datetime.now().strftime('%Y-%m-%d'),
        'current_value': amount,
        'returns': 0
    }
    
    data['investments'].append(new_investment)
    save_data(data)
    return data

def update_investment_value(data, investment_id, current_value):
    for inv in data.get('investments', []):
        if inv.get('id') == investment_id:
            inv['current_value'] = current_value
            inv['returns'] = current_value - inv['amount']
            inv['roi_percentage'] = (inv['returns'] / inv['amount'] * 100) if inv['amount'] > 0 else 0
            save_data(data)
            return data
    
    return data

def get_investment_summary(data):
    investments = data.get('investments', [])
    total_investment_value = sum(inv.get('current_value', 0) for inv in investments)
    total_investment_returns = sum(inv.get('returns', 0) for inv in investments)
    initial_investment = sum(inv.get('amount', 0) for inv in investments)
    overall_roi = (total_investment_returns / initial_investment * 100) if initial_investment > 0 else 0
    return {
        'total_investments_count': len(investments),
        'total_value': total_investment_value,
        'overall_roi_percentage': overall_roi
    }

def generate_report(data):
    expenses = data.get('expenses', [])
    income = data.get('income', [])
    goals = data.get('goals', [])
    investments = data.get('investments', [])
    budget_status = get_budget_status(data)
    
    total_income = sum(i['amount'] for i in income)
    total_expenses = sum(e['amount'] for e in expenses)
    total_savings = total_income - total_expenses
    
    total_investment_value = sum(inv['current_value'] for inv in investments)
    total_investment_returns = sum(inv['returns'] for inv in investments)
    initial_investment = sum(inv['amount'] for inv in investments)
    overall_roi = (total_investment_returns / initial_investment * 100) if initial_investment > 0 else 0
    
    completed_goals = len([g for g in goals if g.get('status') == 'completed'])
    active_goals = len([g for g in goals if g.get('status') == 'active'])
    
    report = {
        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_balance': data.get('balance', 0),
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_savings': total_savings,
            'total_transactions': len(expenses) + len(income)
        },
        'expenses_by_category': get_expenses_by_category(data),
        'income_by_category': get_income_by_category(data),
        'budget_status': budget_status,
        'savings_goals': {
            'total_goals': len(goals),
            'completed': completed_goals,
            'active': active_goals,
            'goals_detail': goals
        },
        'investments': {
            'total_investments': len(investments),
            'total_value': total_investment_value,
            'total_returns': total_investment_returns,
            'overall_roi_percentage': overall_roi,
            'investments_detail': investments
        }
    }
    
    return report

def reset_data():
    default_data = {
        "balance": 0,
        "expenses": [],
        "budget": {},
        "goals": [],
        "investments": [],
        "income": [],
        "settings": {
            "currency": "Rp",
            "theme": "light",
            "monthly_budget_limit": 0
        }
    }
    save_data(default_data)
    return default_data

def calculate_health_score(data):
    now = datetime.now()
    m = get_monthly_summary(data, now.year, now.month)
    
    score = 0
    
    savings_rate = (m['net_savings'] / m['total_income'] * 100) if m['total_income'] > 0 else 0
    if savings_rate >= 30: score += 40
    elif savings_rate > 0: score += (savings_rate / 30) * 40
    
    budget_status = get_budget_status(data)
    over_budget_cats = [c for c, s in budget_status.items() if s['percent_used'] > 100]
    if not over_budget_cats and budget_status: score += 30
    elif budget_status:
        adherence = (len(budget_status) - len(over_budget_cats)) / len(budget_status)
        score += adherence * 30
        
    inv = data.get('investments', [])
    types = len(set([i.get('type') for i in inv]))
    if types >= 3: score += 30
    else: score += (types / 3) * 30
    
    # 4. Emergency Fund Factor (Bonus/Penalty logic can be added)
    
    return min(100, round(score))
