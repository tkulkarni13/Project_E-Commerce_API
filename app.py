from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import fields
from marshmallow import ValidationError
from password import password

# Initialize the Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f'mysql+mysqlconnector://root:{password}@localhost/e_commerce_api'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Database models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)

class OrderProduct(db.Model):
    __tablename__ = 'order_products'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

# Marshmallow schemas
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        fields = ('id', 'name', 'address', 'email')
        include_fk = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price')

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        fields = ('id', 'order_date', 'user_id')
        include_fk = True

class OrderProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OrderProduct
        fields = ('id', 'order_id', 'product_id')
        include_fk = True

# Initialize schemas
user_schema = UserSchema()
users_schema = UserSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
order_product_schema = OrderProductSchema()
order_products_schema = OrderProductSchema(many=True)

# CRUD Endpoints
# Users
# Add new user
@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.json
        new_user = User(name=data['name'], address=data['address'], email=data['email'])
        db.session.add(new_user)
        db.session.commit()
        return user_schema.jsonify(new_user), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

# Get all users
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return users_schema.jsonify(users)

# Get user by ID
@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return user_schema.jsonify(user)

# Update user by ID
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.json
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    db.session.commit()
    return user_schema.jsonify(user)

# Delete user by ID
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})

# Products
# Add new product
@app.route('/products', methods=['POST'])
def create_product():
    try:
        data = request.json
        new_product = Product(name=data['name'], price=data['price'])
        db.session.add(new_product)
        db.session.commit()
        return product_schema.jsonify(new_product), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

# Get all products
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return products_schema.jsonify(products)

# Get product by ID
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    return product_schema.jsonify(product)

# Update product by ID
@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    product.name = data.get('name', product.name)
    product.price = data.get('price', product.price)
    db.session.commit()
    return product_schema.jsonify(product)

# Delete product by ID
@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted'})

# Orders
# Add new order
@app.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        new_order = Order(user_id=data['user_id'], order_date=data['order_date'])
        db.session.add(new_order)
        db.session.commit()
        return order_schema.jsonify(new_order), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

# Add product to order
@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['PUT'])
def add_product_to_order(order_id, product_id):
    order = Order.query.get_or_404(order_id)
    product = Product.query.get_or_404(product_id)

    # Check if the product is already in the order
    existing_order_product = OrderProduct.query.filter_by(order_id=order_id, product_id=product_id).first()
    if existing_order_product:
        return jsonify({'message': 'Product already exists in the order'}), 400

    # Add the product to the order
    new_order_product = OrderProduct(order_id=order_id, product_id=product_id)
    db.session.add(new_order_product)
    db.session.commit()

    return jsonify({'message': 'Product added to the order'}), 200

# Delete product from order
@app.route('/orders/<int:order_id>/remove_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order_product = OrderProduct.query.filter_by(order_id=order_id, product_id=product_id).first_or_404()
    db.session.delete(order_product)
    db.session.commit()
    return jsonify({'message': 'Product removed from the order'}), 200

# Get all orders for a user
@app.route('/orders/user/<int:user_id>', methods=['GET'])
def get_orders_for_user(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    return orders_schema.jsonify(orders)

# Get all products in an order
@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_for_order(order_id):
    order_products = OrderProduct.query.filter_by(order_id=order_id).all()
    product_ids = [op.product_id for op in order_products]
    products = Product.query.filter(Product.id.in_(product_ids)).all()
    return products_schema.jsonify(products)

# Calculate the total price of an order
@app.route('/orders/<int:order_id>/total_price', methods=['GET'])
def calculate_order_total(order_id):
    order_products = OrderProduct.query.filter_by(order_id=order_id).all()
    if not order_products:
        return jsonify({'message': 'No products found in the order'}), 404

    # Calculate the total price
    total_price = sum(Product.query.get(op.product_id).price for op in order_products)
    return jsonify({'order_id': order_id, 'total_price': total_price}), 200

# Get all orders
@app.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return orders_schema.jsonify(orders)

# Main
if __name__ == '__main__':
    # Create the database and tables
    with app.app_context():
        db.create_all()
    app.run(debug=True)