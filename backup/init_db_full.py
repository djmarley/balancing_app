import sqlite3

DATABASE = 'actions.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create table for GL Balance (Query 1)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gl_balance (
            account INTEGER PRIMARY KEY,
            cost_center TEXT,
            branch_name TEXT,
            balance INTEGER,
            date TEXT
        )
    ''')

    # Create table for EZ Teller Balance (Query 2)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ez_teller_balance (
            account INTEGER PRIMARY KEY,
            cost_center TEXT,
            branch_name TEXT,
            balance INTEGER,
            date TEXT
        )
    ''')

    # Create table for branch limits
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS branch_limits (
            cost_center TEXT,
            branch_name TEXT PRIMARY KEY,
            branch_limit INTEGER,
            date_last_updated TEXT
        )
    ''')

    # Create table for mismatch actions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mismatch_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account INTEGER NOT NULL,
            action_date TEXT NOT NULL,
            note TEXT,
            user TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')   

    # Insert dummy data into gl_balance (Query 1)
    gl_data = [
        (1000001001, '001', '001-branch 1', 5000, '2025-02-14'),
        (1000002001, '001', '001-branch 1', 3000, '2025-02-14'),
        (1000001002, '002', '002-branch 2', 5000, '2025-02-14'),
        (1000002002, '002', '002-branch 2', 1000, '2025-02-14'),
        (1000003002, '002', '002-branch 2', 500,  '2025-02-14'),
        (1000011002, '002', '002-branch 2', 94,   '2025-02-14')
    ]
    cursor.executemany('''
        INSERT OR REPLACE INTO gl_balance (account, cost_center, branch_name, balance, date)
        VALUES (?, ?, ?, ?, ?)
    ''', gl_data)

    # Insert dummy data into ez_teller_balance (Query 2)
    ez_data = [
        (1000001001, '001', '001-branch 1', 5000, '2025-02-14'),
        (1000002001, '001', '001-branch 1', 3000, '2025-02-14'),  # This row now matches GL Balance
        (1000001002, '002', '002-branch 2', 5000, '2025-02-14'),
        (1000002002, '002', '002-branch 2', 1000, '2025-02-14'),
        (1000003002, '002', '002-branch 2', 600,  '2025-02-14'),   # Mismatch: 600 vs 500
        (1000011002, '002', '002-branch 2', 94,   '2025-02-14')
    ]
    cursor.executemany('''
        INSERT OR REPLACE INTO ez_teller_balance (account, cost_center, branch_name, balance, date)
        VALUES (?, ?, ?, ?, ?)
    ''', ez_data)

    # Insert dummy data into branch_limits
    branch_limits_data = [
        ('001', '001-branch 1', 127000, '2024-02-14'),
        ('002', '002-branch 2', 275000,  '2021-02-14')
    ]
    cursor.executemany('''
        INSERT OR REPLACE INTO branch_limits (cost_center, branch_name, branch_limit, date_last_updated)
        VALUES (?, ?, ?, ?)
    ''', branch_limits_data)

    conn.commit()
    conn.close()
    print("Database and tables initialized successfully.")

if __name__ == '__main__':
    init_db()
