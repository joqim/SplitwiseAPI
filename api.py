from flask import Flask, jsonify, render_template, redirect, session, url_for, request
from splitwise import Splitwise
from flask_cors import cross_origin
import json
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
import datetime

app = Flask(__name__)
app.secret_key = "joqim"
secret = ''

@app.route("/")
def hello():
    print("inside / dir", flush=True)
    def update_splitwise():
    try:
        print("inside /update in PYTHON SERVER", request.args, flush=True)

        group_id = request.args.get('group_id')
        total_money_paid = request.args.get('total_paid')

        CONSUMER_KEY = request.args.get('CONSUMER_KEY')
        CONSUMER_SECRET = request.args.get('CONSUMER_SECRET')
        API_KEY = request.args.get('API_KEY')

        players = request.args.getlist('players[]')
        parsed_players = [json.loads(player) for player in players]

        sObj = Splitwise(CONSUMER_KEY, CONSUMER_SECRET, api_key=API_KEY)

        expense = Expense()
        expense.setCost(total_money_paid)

        users = []
        for member in parsed_players:
            user = ExpenseUser()
            user.setId(member['id'])

            if float(member['money']) > 0:
                user.setPaidShare(member['money'])
            else:
                money = abs(float(member['money']))
                user.setOwedShare(str(money))

            users.append(user)

        current_date = datetime.datetime.now().strftime("%B-%d")
        day = int(current_date.split("-")[1])
        ordinal_suffix = get_ordinal_suffix(day)
        current_date_with_suffix = current_date.replace(f"{day:02d}", f"{day}{ordinal_suffix}")
        expense.setDescription(current_date_with_suffix)

        expense.setUsers(users)
        expense.setGroupId(group_id)

        sObj.createExpense(expense)
        print("expense updated successfully", expense, flush=True)

        res = dict()
        res['message'] = 'success'

        return jsonify(res), 200
    except Exception as e:
        print("An error occurred:", str(e), flush=True)
        res = dict()
        res['message'] = 'error'
        return jsonify(res), 400

def get_ordinal_suffix(day):
    if 11 <= day <= 13:
        return "th"
    else:
        last_digit = day % 10
        if last_digit == 1:
            return "st"
        elif last_digit == 2:
            return "nd"
        elif last_digit == 3:
            return "rd"
        else:
            return "th"

@app.route('/update')
# @cross_origin()

if __name__ == "__main__":
    app.run(threaded=True, debug=True)
