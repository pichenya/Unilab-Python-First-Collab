from flask import Flask, jsonify, redirect, make_response
from flask_restful import Resource, Api, reqparse
from flask_jwt import JWT, jwt_required
from werkzeug.security import safe_str_cmp
import sqlite3


app = Flask(__name__)
api = Api(app)

mssg_404 = {"message": "მონაცემი ვერ მოიძებნა"}, 404
mssg_400 = {"message": f"მონაცემი id-ით უკვე არსებობს"}, 400
mssg_400_username = {"message": f"მონაცემი ამ username-ით უკვე არსებობს"}
mssg_200 = {"message": "წარმატებით დაემატა პროდუქტი"}, 200
mssg_201 = {"message": "წარმატებით დაემატა იუსერი"}, 200
mssg_update = {"message": "წარმატებით დააფდეითდა პროდუქტი"}, 200
mssg_delete = {"message": "წარმატებით წაიშალა პროდუქტი/იუსერი"}, 200

connection = sqlite3.connect('data.db', check_same_thread=False)

cursor = connection.cursor()

cursor.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY ,username text,password text) ')

cursor.execute(
    'CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY ,brand text,model text,production_date text,price real,quantity real) ')

query_string = 'INSERT INTO users VALUES(?,?,?)'

query_string_items = 'INSERT INTO items VALUES(?,?,?,?,?,?)'

params = [
    (1, 'Admin', 'Password'),
    (2, 'User', 'Pass'),
    (3, 'Monkeh', 'Donkeh')
]

params_items = [
    (
        1,
        "Toyota",
        "Prius",
        "2015/03/17",
        13212.95,
        7
    ),
    (
        2,
        "BMW",
        "e46 m3",
        "1997/12/15",
        14212.95,
        3
    ),
    (
        3,
        "Mazda",
        "ahura",
        "2016/03/17",
        5000,
        2
    )
]


# cursor.executemany(query_string, params)
# cursor.executemany(query_string_items, params_items)
#
# connection.commit()

# connection.close()



class ItemModel:
    def __init__(self, _id, brand, model, production_date, price, quantity):
        self.id = _id
        self.brand = brand
        self.model = model
        self.production_date = production_date
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return f"item {self.id}, {self.brand}, {self.model}"

    @classmethod
    def find_by_item_id(cls, item_id):
        query = 'SELECT * FROM items WHERE id=?'

        result = cursor.execute(query, (item_id,))
        row = result.fetchone()

        if row:
            item = cls(*row)
            result = {item_id: vars(item)}
            connection.commit()
            return result.get(item_id)

    @classmethod
    def insert(cls, dict):
        query = 'INSERT INTO items VALUES(?,?,?,?,?,?)'
        cursor.execute(query, (*dict.values(),))
        connection.commit()
        # connection.close()

    @classmethod
    def update(cls, dict, item_id):
        query = 'UPDATE items SET (id,brand,model,production_date,price,quantity) = (?,?,?,?,?,?) WHERE id=?'
        cursor.execute(query, (*dict.values(), item_id))
        connection.commit()
        # connection.close()


class UserModel:
    def __init__(self, _id, username, password):
        self.id = _id
        self.username = username
        self.password = password

    def __repr__(self):
        return f"user{self.username}"

    @classmethod
    def find_by_username(cls, username):
        query = 'SELECT * FROM users WHERE username=?'

        result = cursor.execute(query, (username,))
        row = result.fetchone()

        if row:
            user = cls(*row)
        else:
            user = None

        return user

    @classmethod
    def find_by_userid(cls, user_id):
        query = 'SELECT * FROM users WHERE id=?'

        result = cursor.execute(query, (user_id,))
        row = result.fetchone()

        if row:
            user = cls(*row)
            result = {user_id: vars(user)}
            connection.commit()
            return result.get(user_id)
        else:
            user = None

        return user

    @classmethod
    def add(cls, params):
        username = UserModel.find_by_username(params.get("username"))
        if username is not None:
            return mssg_400_username

        query_string = 'INSERT INTO users VALUES(?,?,?)'
        cursor.execute(query_string, (*params.values(),))
        connection.commit()
        # connection.close()
        return "წარმატებით დაემატა იუზერი"

    @classmethod
    def update(cls, dict, user_id):
        query = 'UPDATE users SET (id,username,password) = (?,?,?) WHERE id=?'
        cursor.execute(query, (*dict.values(), user_id))
        connection.commit()
        # connection.close()


def auth(username, password):
    user = UserModel.find_by_username(username)
    if user and safe_str_cmp(user.password, password):
        return user


def identity(payload):
    user_id = payload['identity']
    return UserModel.find_by_userid(user_id)


jwt = JWT(app, auth, identity)

app.config["JWT_SECRET_KEY"] = "Donkeh"



class RegisterUser(Resource):
    UserParser = reqparse.RequestParser()
    UserParser.add_argument("id", type=int, required=True, help="id should be a string")
    UserParser.add_argument("username", type=str, required=True, help="username should be a string")
    UserParser.add_argument("password", type=str, required=True, help="password should be string")

    def post(self):
        params = RegisterUser.UserParser.parse_args()
        return UserModel.add(params)


class Home(Resource):
    def get(self):
        return redirect('https://github.com/LilDiabetes/LilDiabetes')


class ItemList(Resource):

    @jwt_required()
    def get(self, item_id):
        if item_id == 000:
            query = "SELECT * FROM items"
            result = cursor.execute(query, ())
            items = result.fetchall()
            return make_response(jsonify(items), 200)

    @jwt_required()
    def delete(self, item_id):
        if item_id == 111:
            query = "DELETE FROM items"
            cursor.execute(query, ())
            connection.commit()
            return mssg_delete


class Item(Resource):
    ItemParser = reqparse.RequestParser()
    ItemParser.add_argument("id", type=int, required=True, help="id should be an integer")
    ItemParser.add_argument("brand", type=str, required=True, help="name should be a string")
    ItemParser.add_argument("model", type=str, required=True, help="model should be string")
    ItemParser.add_argument("production_date", type=str, required=True, help="production_date should be string")
    ItemParser.add_argument("price", type=float, required=True, help="price should be float")
    ItemParser.add_argument("quantity", type=int, required=True, help="quantity should be integer")

    @jwt_required()
    def get(self, item_id):
        item = ItemModel.find_by_item_id(item_id)
        if item:
            return make_response(jsonify(item))
        else:
            return mssg_404

    @jwt_required()
    def post(self, item_id):
        item = ItemModel.find_by_item_id(item_id)
        if not item:
            params = Item.ItemParser.parse_args()
            ItemModel.insert(params)
            return mssg_200
        return mssg_400

    @jwt_required()
    def put(self, item_id):
        params = Item.ItemParser.parse_args()
        item = ItemModel.find_by_item_id(item_id)
        if item:
            ItemModel.update(params, item_id)
            return mssg_update
        else:
            ItemModel.insert(params)
            return mssg_200

    @jwt_required()
    def delete(self, item_id):
        item = ItemModel.find_by_item_id(item_id)
        if item:
            query = "DELETE  FROM items WHERE id=?"
            cursor.execute(query, (item_id,))
            connection.commit()
            # connection.close()
            return mssg_delete
        else:
            return mssg_404


class User(Resource):
    UserParser = reqparse.RequestParser()
    UserParser.add_argument("id", type=int, required=True, help="id should be an integer")
    UserParser.add_argument("username", type=str, required=True, help="username should be a string")
    UserParser.add_argument("password", type=str, required=True, help="password should be string")

    @jwt_required()
    def get(self, user_id):
        user = UserModel.find_by_userid(user_id)
        if user:
            return make_response(jsonify(user))
        else:
            return mssg_404

    @jwt_required()
    def post(self, user_id):
        user = UserModel.find_by_userid(user_id)
        if not user:
            params = User.UserParser.parse_args()
            UserModel.add(params)
            return mssg_201
        return mssg_400

    @jwt_required()
    def put(self, user_id):
        params = User.UserParser.parse_args()
        user = UserModel.find_by_userid(user_id)
        if user:
            UserModel.update(params, user_id)
            return mssg_update
        else:
            UserModel.add(params)
            return mssg_200

    @jwt_required()
    def delete(self, user_id):
        user = UserModel.find_by_userid(user_id)
        if user:
            query = "DELETE  FROM users WHERE id=?"
            cursor.execute(query, (user_id,))
            connection.commit()
            # connection.close()
            return mssg_delete
        else:
            return mssg_404


api.add_resource(ItemList, '/itemlist/<int:item_id>')
api.add_resource(Item, '/item/<int:item_id>')
api.add_resource(User, '/user/<int:user_id>')
api.add_resource(Home, '/')
api.add_resource(RegisterUser, '/register')

if __name__ == '__main__':
    app.run(debug=True)
