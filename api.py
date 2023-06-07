from flask import Flask, jsonify, request, session, redirect
from flask_cors import CORS
from splitwise import Splitwise
from flask_cors import cross_origin
import json
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = "joqim"
secret = ''

# Enable CORS for all routes
CORS(app)

load_dotenv()  # Load environment variables from .env file

@app.route("/auth_code")
def auth():
    try:
        print("Inside /auth_code in Flask", flush=True)
        
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")

        sObj = Splitwise(consumer_key, consumer_secret)
        url, secret = sObj.getAuthorizeURL()
        
        print("url", url, flush=True)
        print("secret", secret, flush=True)
        
        # Store secret so you can retrieve it later
        session['secret'] = secret
        print("session", session)

        res = {"redirect_url": url, "secret": secret}
        return jsonify(res), 200

    except Exception as e:
        print("An error occurred in auth_code:", str(e), flush=True)
        res = {"message": "error"}
        return jsonify(res), 400

@app.route("/access_token")
def oauth_callback():
    try:
        print("inside /access_token - session")
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')
        secret = request.args.get('secret')

        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        
        sObj = Splitwise(consumer_key, consumer_secret)
        session['secret'] = secret
        
        print("session", session, consumer_key, consumer_secret, flush=True)
        access_token = sObj.getAccessToken(oauth_token, session['secret'], oauth_verifier)
        
        print("access token", access_token, flush=True)
        session['access_token'] = access_token

        # sObj.setAccessToken(session['access_token'])
        # group = sObj.getGroup(28857816)
        # print("group", group.getMembers()[0], flush=True)
        
        res = {"token": access_token}
        return jsonify(res), 200

    except Exception as e:
        print("An error occurred in oauth_callback:", str(e), flush=True)
        res = {"message": "error"}
        return jsonify(res), 400

@app.route('/groups', methods=['GET'])
def groups():
    try:
        print("Inside /groups", request.args, flush=True)
        
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        
        oauth_token = request.args.get('oauth_token')
        oauth_token_secret = request.args.get('oauth_token_secret')
        
        access_token = {
            "oauth_token": oauth_token,
            "oauth_token_secret": oauth_token_secret
        }
        
        session['access_token'] = access_token
        print("session", session, flush=True)
        
        sObj = Splitwise(consumer_key, consumer_secret)
        sObj.setAccessToken(session['access_token'])
        
        groups = sObj.getGroups()

        # Convert the groups to a JSON-serializable format
        serialized_groups = []
        for group in groups:
            serialized_group = {
                'id': group.id,
                'name': group.name,
                # Include any other required attributes
            }
            serialized_groups.append(serialized_group)

        print("groups", serialized_groups, flush=True)
        # Create the response dictionary
        response = {"groups": serialized_groups}

        # Return the response as JSON
        return json.dumps(response), 200
    
    except Exception as e:
        print("An error occurred:", str(e), flush=True)
        res = {"message": "error"}
        return jsonify(res), 400

@app.route('/players', methods=['GET'])
def players():
    try:
        print("Inside /players", request.args, flush=True)
        
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        
        oauth_token = request.args.get('oauth_token')
        oauth_token_secret = request.args.get('oauth_token_secret')
        groupId = request.args.get('group')
        
        access_token = {
            "oauth_token": oauth_token,
            "oauth_token_secret": oauth_token_secret
        }
        
        session['access_token'] = access_token
        print("session", session, flush=True)
        
        sObj = Splitwise(consumer_key, consumer_secret)
        sObj.setAccessToken(session['access_token'])
        group = sObj.getGroup(groupId)

        # Convert the groups to a JSON-serializable format
        serialized_players = []
        for player in group.getMembers():
            serialized_player = {
                'id': player.id,
                'email': player.email,
                'first_name': player.first_name,
                'last_name': player.last_name
            }
            serialized_players.append(serialized_player)

        print("players", serialized_players, flush=True)
        # Create the response dictionary
        response = {"players": serialized_players}

        # Return the response as JSON
        return json.dumps(response), 200
    
    except Exception as e:
        print("An error occurred:", str(e), flush=True)
        res = {"message": "error"}
        return jsonify(res), 400
    
@app.route("/update")
def update_splitwise():
    try:
        print("inside /update in PYTHON SERVER", request.args, flush=True)

        group_id = request.args.get('group_id')
        total_money_paid = request.args.get('total_paid')
        
        oauth_token = request.args.get('oauth_token')
        oauth_token_secret = request.args.get('oauth_token_secret')
                
        access_token = {
            "oauth_token": oauth_token,
            "oauth_token_secret": oauth_token_secret
        }
        
        session['access_token'] = access_token
        print("session", session, flush=True)
        
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        
        sObj = Splitwise(consumer_key, consumer_secret)
        sObj.setAccessToken(session['access_token'])

        players = request.args.getlist('players[]')
        parsed_players = [json.loads(player) for player in players]

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

@app.route("/test")
def test():
    try:
        print("inside /test in PYTHON SERVER", request.args, flush=True)

        res = dict()
        res['message'] = 'success'

        return jsonify(res), 200
    except Exception as e:
        print("An error occurred:", str(e), flush=True)
        res = dict()
        res['message'] = 'error'
        return jsonify(res), 400
    
if __name__ == "__main__":
    app.run(threaded=True, debug=True)