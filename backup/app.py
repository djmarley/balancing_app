from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'actions.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.template_filter('currency')
def currency_filter(value):
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value

@app.route('/')
def index():
    conn = get_db_connection()

    # Get selected date from user input
    report_date = request.args.get('report_date')

    # If no date is provided, use the most recent date from gl_balance
    if not report_date:
        report_date_query = conn.execute("SELECT MAX(date) FROM gl_balance").fetchone()
        report_date = report_date_query[0] if report_date_query[0] else "Unknown Date"

    # Read Query 1 data (GL Balance) for the selected date
    gl_data = conn.execute("SELECT * FROM gl_balance WHERE date = ?", (report_date,)).fetchall()
    # Read Query 2 data (EZ Teller Balance) for the selected date
    ez_data = conn.execute("SELECT * FROM ez_teller_balance WHERE date = ?", (report_date,)).fetchall()
    # Read branch limits data
    branch_limits_data_raw = conn.execute("SELECT * FROM branch_limits").fetchall()

    # Fetch recorded actions for the selected date
    recorded_actions = conn.execute(
        "SELECT account, user, timestamp FROM mismatch_actions WHERE action_date = ?",
        (report_date,)
    ).fetchall()

    conn.close()

    # Convert actions to a dictionary {account: {user, timestamp}}
    actions = {row["account"]: {"user": row["user"], "timestamp": row["timestamp"]} for row in recorded_actions}

    # Convert rows to tuples
    data1 = [ (row['account'], row['cost_center'], row['branch_name'], row['balance'], row['date']) for row in gl_data ]
    data2 = [ (row['account'], row['cost_center'], row['branch_name'], row['balance'], row['date']) for row in ez_data ]
    branch_limits_data = [ (row['cost_center'], row['branch_name'], row['branch_limit'], row['date_last_updated']) for row in branch_limits_data_raw ]

    # ✅ Initialize combined list before using it
    combined = []
    dict1 = {row[0]: row for row in data1}
    dict2 = {row[0]: row for row in data2}

    all_accounts = set(dict1.keys()) | set(dict2.keys())
    for account in all_accounts:
        row1 = dict1.get(account)
        row2 = dict2.get(account)
        is_match = (row1 == row2) if (row1 and row2) else False

        combined.append({
            'account': account,
            'table1': row1,
            'table2': row2,
            'match': is_match
        })

    # ✅ Group accounts by branch
    branches = {}
    for row in combined:
        if row['table1']:
            branch = row['table1'][2].strip().lower()
        elif row['table2']:
            branch = row['table2'][2].strip().lower()
        else:
            branch = "unknown branch"
        branches.setdefault(branch, []).append(row)

    # Create normalized branch limits mapping
    branch_limits = {row[1].strip().lower(): row[2] for row in branch_limits_data}

    # ✅ Compute summary for each branch
    branch_summary = {}
    for branch, accounts in branches.items():
        total_balance_q1 = 0
        total_balance_q2 = 0
        branch_match = True
        for account in accounts:
            if account['table1']:
                total_balance_q1 += account['table1'][3]
            if account['table2']:
                total_balance_q2 += account['table2'][3]
            if not account['match']:
                branch_match = False

        branch_limit = branch_limits.get(branch, "N/A")

        branch_summary[branch] = {
            'accounts': accounts,
            'total_balance_q1': total_balance_q1,
            'total_balance_q2': total_balance_q2,
            'match': branch_match,
            'branch_limit': branch_limit
        }

    return render_template('index.html', branch_summary=branch_summary, report_date=report_date, actions=actions)



@app.route('/record/<int:account>', methods=['GET', 'POST'])
def record(account):
    # For simplicity, using a static report_date; adjust as needed.
    report_date = "2025-02-14"
    conn = get_db_connection()

    if request.method == 'POST':
        note = request.form.get('note', '')
        conn.execute(
            "INSERT INTO mismatch_actions (account, action_date, note) VALUES (?, ?, ?)",
            (account, report_date, note)
        )
        conn.commit()
        conn.close()
        flash(f"Action recorded for account {account}.", "success")
        return redirect(url_for('index'))
    else:
        action = conn.execute(
            "SELECT * FROM mismatch_actions WHERE account = ? AND action_date = ? ORDER BY timestamp DESC LIMIT 1",
            (account, report_date)
        ).fetchone()
        conn.close()
        note = action['note'] if action else ""
        return render_template('record.html', account=account, report_date=report_date, note=note)

if __name__ == '__main__':
    app.run(debug=True)
