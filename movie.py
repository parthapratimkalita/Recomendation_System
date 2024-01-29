import json
from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from surprise import SVD
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import cross_validate
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, jsonify, session
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SECRET_KEY'] = '1hdj@34kf'
db = SQLAlchemy(app)



# Set up the LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    visit_count = db.Column(db.Integer, default=0)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    review = db.Column(db.Text, nullable=False)

@app.route('/')
def start():
    return render_template('home.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            login_user(user)  # log in the user with Flask-Login
            session['user_id'] = user.id  # set user_id in session
            user.visit_count += 1
            db.session.commit()
            return redirect(url_for('home'))
    return render_template('login.html')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/profile')
def profile():
    if current_user.is_authenticated:
        user_info = {
            'username': current_user.username,
            # add any other user fields you want to display
        }
        return jsonify(user_info)
    else:
        return jsonify(None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/rate_movie', methods=['POST'])
def rate_movie():
    user_id = session['user_id']
    movie_id = request.form['movie_id']
    rating = request.form['rating']
    rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
    db.session.add(rating)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/submit_review', methods=['POST'])
def submit_review():
    movie_id = request.form.get('movieId')
    user_id = session['user_id']
    rating = request.form.get('rating')
    review = request.form.get('review')
    review_obj = Review(user_id=user_id, movie_id=movie_id, rating=rating, review=review)
    db.session.add(review_obj)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/recommend')
def recommend():
    user_id = session['user_id']
    ratings = Rating.query.all()
    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(ratings[['user_id', 'movie_id', 'rating']], reader)
    trainset = data.build_full_trainset()
    algo = SVD()
    algo.fit(trainset)
    predictions = []
    for movie_id in Movie.query.all():
        prediction = algo.predict(user_id, movie_id)
        predictions.append((movie_id, prediction.est))
    predictions.sort(key=lambda x: x[1], reverse=True)
    recommended_movie_ids = [movie_id for movie_id, _ in predictions[:10]]
    return render_template('recommend.html', movies=Movie.query.filter(Movie.id.in_(recommended_movie_ids)))

@app.route('/df_merged.json')
def serve_df_merged():
    return app.send_static_file('df_merged.json')


@app.route('/notification')
def notification():
    # Get the current user
    user = db.session.get(User, session['user_id'])

    if user and user.visit_count == 1:
        # Return a system-generated "Hello" notification
        notification = '''Thanks for trying our app. Now we are recomending you movies based on previous ratings, after you will review some of them it will be more accurate according to your taste and content selection.'''
    else:
        # Return an empty notification if the user's visit count is not one
        notification = ''

    return jsonify({'notification': notification})

@app.route('/review', methods=['GET', 'POST'])
def review():
    if request.method == 'POST':
        data = request.get_json()
        user_id = session['user_id']
        movie_id = data['movieId']
        session['data'] = data
        existing_review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        print(existing_review)
        if existing_review:
            # If a review by this user for this movie already exists, return a 409 status code
            return jsonify('Existing review found')
        else:
            # Otherwise, store the data in the session and return it
            return jsonify(data)
    else:  # GET request
        data = session.get('data')
        return render_template('review.html', data=data)

@app.route('/review_found', methods=['GET'])  
def review_found():
        data = session.get('data')
        print(data)
        movie_id = data['movieId']
        user_id = session['user_id']
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++++++')
        existing_reviews = Review.query.filter_by(user_id=user_id, movie_id=movie_id).all()
        for review in existing_reviews:
            data['your_rating'] = review.rating
            data['your_review'] = review.review
            return render_template('review.html', data=data)

        

if __name__ == '__main__':
    
    with app.app_context():
        db.create_all()
    app.run(debug=True)

    