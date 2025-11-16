from flask import Flask, render_template, request, jsonify, session, send_file
from models import db, Menu, Order, OrderItem
from datetime import datetime, timedelta
import os
import qrcode
from io import BytesIO
import base64
import secrets
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
db_uri = os.environ.get('DATABASE_URL') or 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images'

db.init_app(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize cart in session
@app.before_request
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

@app.route('/')
def index():
    menu_items = Menu.query.all()
    return render_template('index.html', menu_items=menu_items)

@app.route('/api/get-cart', methods=['GET'])
def get_cart():
    cart = session.get('cart', [])
    return jsonify({'success': True, 'cart': cart})

@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    data = request.json
    menu_id = data.get('menu_id')
    quantity = int(data.get('quantity', 1))
    
    menu_item = db.session.get(Menu, menu_id)
    if not menu_item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    cart = session.get('cart', [])
    
    # Check if item already in cart
    item_found = False
    for item in cart:
        if item['menu_id'] == menu_id:
            item['quantity'] += quantity
            item_found = True
            break
    
    if not item_found:
        cart.append({
            'menu_id': menu_id,
            'name': menu_item.name,
            'price': menu_item.price,
            'quantity': quantity,
            'image_path': menu_item.image_path
        })
    
    session['cart'] = cart
    return jsonify({'success': True, 'cart': cart})

@app.route('/api/update-cart', methods=['POST'])
def update_cart():
    data = request.json
    menu_id = data.get('menu_id')
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', [])
    
    for item in cart:
        if item['menu_id'] == menu_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            break
    
    session['cart'] = cart
    return jsonify({'success': True, 'cart': cart})

@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():
    data = request.json
    menu_id = data.get('menu_id')
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['menu_id'] != menu_id]
    
    session['cart'] = cart
    return jsonify({'success': True, 'cart': cart})

@app.route('/api/clear-cart', methods=['POST'])
def clear_cart():
    session['cart'] = []
    return jsonify({'success': True, 'cart': []})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', [])
    
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400
    
    # Calculate total
    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    
    # Generate order number
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)[:4].upper()}"
    
    # Create order
    order = Order(
        order_number=order_number,
        total_amount=total_amount,
        status='completed'
    )
    db.session.add(order)
    db.session.flush()
    
    # Create order items
    for item in cart:
        order_item = OrderItem(
            order_id=order.id,
            menu_id=item['menu_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)
    
    db.session.commit()
    
    # Clear cart
    session['cart'] = []
    
    return jsonify({
        'success': True,
        'order': order.to_dict()
    })

@app.route('/api/generate-qr', methods=['POST'])
def generate_qr():
    data = request.json
    order_number = data.get('order_number')
    total_amount = data.get('total_amount')
    
    # Create UPI payment QR code data (UPI QR format)
    # Format: upi://pay?pa=<UPI_ID>&pn=<PAYEE_NAME>&am=<AMOUNT>&cu=INR&tn=<TRANSACTION_NOTE>
    upi_id = "restaurant@paytm"  # Replace with actual UPI ID
    payee_name = "Restaurant"
    amount = f"{total_amount:.2f}"
    transaction_note = f"Order {order_number}"
    
    qr_data = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount}&cu=INR&tn={transaction_note}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return jsonify({
        'success': True, 
        'qr_code': f'data:image/png;base64,{img_str}',
        'upi_id': upi_id
    })

@app.route('/manage-menu')
def manage_menu():
    menu_items = Menu.query.all()
    return render_template('manage_menu.html', menu_items=menu_items)

@app.route('/api/menu', methods=['POST'])
def create_menu():
    data = request.form
    name = data.get('name')
    price = float(data.get('price'))
    description = data.get('description', '')
    
    # Handle image - either file upload or URL
    image_path = None
    image_url = data.get('image_url', '').strip()
    
    if image_url:
        # Store URL directly (for external images)
        image_path = image_url
    elif 'image' in request.files:
        file = request.files['image']
        if file.filename:
            filename = f"{secrets.token_hex(8)}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_path = f"images/{filename}"
    
    menu_item = Menu(
        name=name,
        price=price,
        description=description,
        image_path=image_path
    )
    
    db.session.add(menu_item)
    db.session.commit()
    
    return jsonify({'success': True, 'menu_item': menu_item.to_dict()})

@app.route('/api/menu/<int:menu_id>', methods=['PUT'])
def update_menu(menu_id):
    menu_item = db.session.get(Menu, menu_id)
    if not menu_item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    data = request.form
    menu_item.name = data.get('name', menu_item.name)
    menu_item.price = float(data.get('price', menu_item.price))
    menu_item.description = data.get('description', menu_item.description)
    menu_item.updated_at = datetime.utcnow()
    
    # Handle image - either file upload or URL
    image_url = data.get('image_url', '').strip()
    
    if image_url:
        # Store URL directly (for external images)
        menu_item.image_path = image_url
    elif 'image' in request.files:
        file = request.files['image']
        if file.filename:
            filename = f"{secrets.token_hex(8)}_{file.filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            menu_item.image_path = f"images/{filename}"
    
    db.session.commit()
    
    return jsonify({'success': True, 'menu_item': menu_item.to_dict()})

@app.route('/api/menu/<int:menu_id>', methods=['DELETE'])
def delete_menu(menu_id):
    menu_item = db.session.get(Menu, menu_id)
    if not menu_item:
        return jsonify({'error': 'Menu item not found'}), 404
    
    db.session.delete(menu_item)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/sales-report')
def sales_report():
    return render_template('sales_report.html')

@app.route('/api/sales-data')
def sales_data():
    month = request.args.get('month')
    year = request.args.get('year')
    
    if month and year:
        start_date = datetime(int(year), int(month), 1)
        if int(month) == 12:
            end_date = datetime(int(year) + 1, 1, 1)
        else:
            end_date = datetime(int(year), int(month) + 1, 1)
        
        orders = Order.query.filter(
            Order.order_date >= start_date,
            Order.order_date < end_date
        ).all()
    else:
        # Default to current month
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1)
        else:
            end_date = datetime(now.year, now.month + 1, 1)
        
        orders = Order.query.filter(
            Order.order_date >= start_date,
            Order.order_date < end_date
        ).all()
    
    total_sales = sum(order.total_amount for order in orders)
    total_orders = len(orders)
    
    # Top selling items
    from sqlalchemy import func
    top_items = db.session.query(
        Menu.name,
        func.sum(OrderItem.quantity).label('total_quantity'),
        func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
    ).join(OrderItem, Menu.id == OrderItem.menu_id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.order_date >= start_date, Order.order_date < end_date)\
     .group_by(Menu.name)\
     .order_by(func.sum(OrderItem.quantity).desc())\
     .limit(10).all()
    
    # Daily breakdown
    daily_sales = db.session.query(
        func.date(Order.order_date).label('date'),
        func.sum(Order.total_amount).label('daily_total'),
        func.count(Order.id).label('order_count')
    ).filter(Order.order_date >= start_date, Order.order_date < end_date)\
     .group_by(func.date(Order.order_date))\
     .order_by(func.date(Order.order_date)).all()
    
    return jsonify({
        'total_sales': total_sales,
        'total_orders': total_orders,
        'top_items': [{'name': item[0], 'quantity': item[1], 'revenue': float(item[2])} for item in top_items],
        'daily_sales': [{'date': str(item[0]), 'total': float(item[1]), 'orders': item[2]} for item in daily_sales]
    })

def generate_menu_images():
    """Generate placeholder images for menu items if they don't exist"""
    menu_items_data = [
        {'name': 'Idly', 'color': (255, 255, 240), 'text_color': (139, 69, 19)},
        {'name': 'Dosa', 'color': (255, 218, 185), 'text_color': (139, 69, 19)},
        {'name': 'Poori', 'color': (255, 215, 0), 'text_color': (139, 69, 19)},
        {'name': 'Vada', 'color': (222, 184, 135), 'text_color': (139, 69, 19)},
        {'name': 'Tea', 'color': (139, 69, 19), 'text_color': (255, 255, 255)},
        {'name': 'Coffee', 'color': (101, 67, 33), 'text_color': (255, 255, 255)},
        {'name': 'Milk', 'color': (255, 255, 255), 'text_color': (0, 0, 0)},
        {'name': 'Boost', 'color': (255, 140, 0), 'text_color': (255, 255, 255)},
    ]
    
    for item in menu_items_data:
        filename = f"{item['name'].lower()}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Only create if image doesn't exist
        if not os.path.exists(filepath):
            width, height = 400, 300
            image = Image.new('RGB', (width, height), item['color'])
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("arial.ttf", 60)
            except:
                try:
                    font = ImageFont.truetype("arial.ttf", 40)
                except:
                    font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), item['name'], font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            draw.text((x + 2, y + 2), item['name'], fill=(0, 0, 0, 128), font=font)
            draw.text((x, y), item['name'], fill=item['text_color'], font=font)
            draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=3)
            
            image.save(filepath, 'JPEG', quality=85)
            print(f"Generated image: {filepath}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Generate images for menu items
        generate_menu_images()
        
        # Pre-populate menu if empty
        if Menu.query.count() == 0:
            default_items = [
                {'name': 'Idly', 'price': 30.0, 'image_path': 'https://images.unsplash.com/photo-1589301760014-eed999baf231?w=400&h=300&fit=crop'},
                {'name': 'Dosa', 'price': 50.0, 'image_path': 'https://images.unsplash.com/photo-1589090190199-f61b1a626480?w=400&h=300&fit=crop'},
                {'name': 'Poori', 'price': 40.0, 'image_path': 'https://images.unsplash.com/photo-1567620905732-2d1ec7ab7445?w=400&h=300&fit=crop'},
                {'name': 'Vada', 'price': 25.0, 'image_path': 'https://images.unsplash.com/photo-1599599810694-b3ea7c2b1a13?w=400&h=300&fit=crop'},
                {'name': 'Tea', 'price': 15.0, 'image_path': 'https://images.unsplash.com/photo-1597318972826-c0a1d3a76f6b?w=400&h=300&fit=crop'},
                {'name': 'Coffee', 'price': 20.0, 'image_path': 'https://images.unsplash.com/photo-1559056199-641a0ac8b3f4?w=400&h=300&fit=crop'},
                {'name': 'Milk', 'price': 18.0, 'image_path': 'https://images.unsplash.com/photo-1608270861620-7476fad8b5f9?w=400&h=300&fit=crop'},
                {'name': 'Boost', 'price': 25.0, 'image_path': 'https://images.unsplash.com/photo-1577003833154-a92bdbd3e8a8?w=400&h=300&fit=crop'}
            ]
            
            for item_data in default_items:
                menu_item = Menu(**item_data)
                db.session.add(menu_item)
            
            db.session.commit()
            print("Default menu items added!")
    
    app.run(debug=True)

