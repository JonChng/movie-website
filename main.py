from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
import os
import dotenv
from sqlalchemy import desc

dotenv.load_dotenv()
api = os.environ["API"]
endpoint1 = "https://api.themoviedb.org/3/search/movie"
endpoint2 = "https://api.themoviedb.org/3/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    ranking = db.Column(db.Integer)

    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Book {self.title}>'
db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()


class LoginForm(FlaskForm):
    rating = StringField('Rating', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField("Update")

class AddForm(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField("Search")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movies)):
        print(movies[i])
        movies[i].ranking = len(movies[i::])
    return render_template("index.html", movies=movies)

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = LoginForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        movies = db.session.query(Movie).all()
        return redirect(url_for("home"))
    else:
        return render_template("edit.html", form=form, movie=movie)

@app.route("/delete", methods=['GET','POST'])
def delete():
    movie_id = request.args.get("id")
    print(movie_id)
    Movie.query.filter_by(id=movie_id).delete()
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=['GET','POST'])
def add():
    form = AddForm()

    if form.validate_on_submit():
        params = {
            "api_key": api,
            "query": form.movie_title.data
        }

        data = requests.get(endpoint1, params=params)
        data.raise_for_status()
        movies = data.json()['results']

        return render_template('select.html', movies=movies)

    return render_template("add.html", form=form)

@app.route("/add1", methods=['GET','POST'])
def final_add():
    id = request.args.get("id")
    params = {
        "api_key": api,
        "movie_id": id
    }
    response = requests.get(url = f"https://api.themoviedb.org/3/movie/{id}?api_key={api}&language=en-US")
    response.raise_for_status()
    data = response.json()
    new_movie = Movie(
        title=data["title"],
        # The data in release_date includes month and day, we will want to get rid of.
        year=data["release_date"].split("-")[0],
        img_url=f"https://image.tmdb.org/t/p/original{data['poster_path']}",
        description=data["overview"],
        rating=0,
        review="None"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))



if __name__ == '__main__':
    app.run(port=8000, debug=True)
