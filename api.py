from flask import Flask, jsonify, render_template, redirect, session, url_for, request
from splitwise import Splitwise
import config as Config
from flask_cors import cross_origin
import json
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
import webbrowser
import datetime

app = Flask(__name__)
app.secret_key = "joqim"
secret = ''

@app.route("/")
def hello():
    return "Hello, Vercel!!"

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

@app.route('/update', methods=["POST"])
@cross_origin()
def update_splitwise():
    try:
        print("inside /update in PYTHON SERVER", flush=True)

        CONSUMER_KEY = request.json['CONSUMER_KEY']
        CONSUMER_SECRET = request.json['CONSUMER_SECRET']
        API_KEY = request.json['API_KEY']
        #print("api", API_KEY, flush=True)

        group_id = request.json['group_id']

        sObj = Splitwise(CONSUMER_KEY, CONSUMER_SECRET, api_key=API_KEY)

        # joe Id - 43611566
        # pras Id = 30618134
        # Test group Id - 44555421

        members = request.json['players']
        #print("members", members, flush=True)
        #print("first member", members[0]['id'], flush=True)

        total_money_paid = request.json['total_paid']
        #print("total_money_paid", total_money_paid, flush=True)

        expense = Expense()
        expense.setCost(total_money_paid)
        # expense.setCost('2.0')

        users = []
        for member in members:
            user = ExpenseUser()
            user.setId(member['id'])

            #print("money value", member['money'], flush=True)
            if float(member['money']) > 0:
                user.setPaidShare(member['money'])
                # user.setPaidShare('2.00')
            else:
                money = abs(float(member['money']))
                #print("money negative", money, flush=True)
                user.setOwedShare(str(money))
                # user.setOwedShare('2.00')

            users.append(user)

        # Set description as current date with ordinal suffix
        current_date = datetime.datetime.now().strftime("%B-%d")
        day = int(current_date.split("-")[1])
        ordinal_suffix = get_ordinal_suffix(day)
        current_date_with_suffix = current_date.replace(f"{day:02d}", f"{day}{ordinal_suffix}")
        #print("desc", current_date_with_suffix)
        expense.setDescription(current_date_with_suffix)

        expense.setUsers(users)
        expense.setGroupId(group_id)

        sObj.createExpense(expense)

        print("expense updated successfully", flush=True)

        res = dict()
        res['message'] = 'success'

        return jsonify(res), 200
    except Exception as e:
        print("An error occurred:", str(e), flush=True)
        res = dict()
        res['message'] = 'error'
        return jsonify(res), 400

if __name__ == "__main__":
    app.run(threaded=True,debug=True)