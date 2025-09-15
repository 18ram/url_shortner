import os
import psycopg2
import random, string
from flask import Flask, render_template, request, redirect, url_for, flash

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallbacksecret")

# PostgreSQL connection
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dbname=os.getenv("DB_NAME"),
)
cursor = conn.cursor()

# Homepage: form + results
@app.route("/", methods=["GET", "POST"])
def index():
    short_url = None
    if request.method == "POST":
        long_url = request.form["long_url"].strip()
        company_name = request.form["company_name"].strip().lower()

        if not long_url or not company_name:
            flash("Please provide both URL and company name.", "danger")
            return redirect(url_for("index"))

        # Generate unique short code
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
            cursor.execute("SELECT id FROM urls WHERE short_code=%s AND company=%s", (code, company_name))
            if not cursor.fetchone():
                break

        # Save
        cursor.execute(
            "INSERT INTO urls (long_url, short_code, company) VALUES (%s, %s, %s)",
            (long_url, code, company_name)
        )
        conn.commit()

        # Use your Render domain instead of 127.0.0.1
        base_url = request.host_url  # dynamically picks domain (e.g. https://yourapp.onrender.com/)
        short_url = f"{base_url}{company_name}/{code}"
        flash("Short URL created successfully!", "success")

    return render_template("index.html", short_url=short_url)

# Redirect
@app.route("/<company>/<short_code>")
def redirect_url(company, short_code):
    cursor.execute("SELECT long_url FROM urls WHERE short_code=%s AND company=%s", (short_code, company))
    result = cursor.fetchone()
    if result:
        return redirect(result[0])
    else:
        return "Invalid or expired short URL", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
