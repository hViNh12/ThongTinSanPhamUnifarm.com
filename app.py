from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import os, time
import qrcode
from io import BytesIO

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ================= CẤU HÌNH DATABASE =================
# Khi deploy Render / Railway / Heroku → dùng DATABASE_URL do server cấp
# Khi chạy local → fallback sang SQLite (data.db)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///data.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ================= MODEL =================
class ProductInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=True)
    image = db.Column(db.String(200), nullable=True)

# Tạo bảng và dữ liệu mặc định
with app.app_context():
    db.create_all()
    if not ProductInfo.query.first():
        default = ProductInfo(date="Chưa cập nhật", image="chuoi.png")
        db.session.add(default)
        db.session.commit()

# ================= CẤU HÌNH KHÁC =================
ADMIN_PASSWORD = "@@unifarm12"
UPLOAD_FOLDER = "static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
DEFAULT_IMAGE = "chuoi.png"

# ================= HÀM HỖ TRỢ =================
def get_info():
    return ProductInfo.query.first()

def save_date(new_date):
    info = get_info()
    info.date = new_date
    db.session.commit()

def save_image_name(filename):
    info = get_info()
    info.image = filename
    db.session.commit()

# ================= ROUTES =================

# Trang chính
@app.route("/")
def index():
    info = get_info()
    return render_template("index.html", ngay=info.date, image_file=info.image)

# Trang admin
@app.route("/admin")
def admin():
    return render_template("admin.html")

# Cập nhật ngày
@app.route("/update-date", methods=["POST"])
def update_date():
    password = request.form.get("password", "")
    new_date = request.form.get("new_date", "")

    if password != ADMIN_PASSWORD:
        flash("Sai mật khẩu! Không thể cập nhật ngày.")
        return redirect(url_for("admin"))

    save_date(new_date)
    flash("Cập nhật ngày thành công!")
    return redirect(url_for("index"))

# Đổi ảnh sản phẩm
@app.route("/upload-image", methods=["POST"])
def upload_image():
    password = request.form.get("password", "")

    if password != ADMIN_PASSWORD:
        flash("Sai mật khẩu! Không thể đổi ảnh.")
        return redirect(url_for("admin"))

    if "new_image" not in request.files:
        flash("Chưa chọn file ảnh.")
        return redirect(url_for("admin"))

    file = request.files["new_image"]
    if file.filename == "":
        flash("Tên file không hợp lệ.")
        return redirect(url_for("admin"))

    # Xoá ảnh cũ
    info = get_info()
    old_image = info.image
    old_path = os.path.join(app.config["UPLOAD_FOLDER"], old_image)
    if old_image != DEFAULT_IMAGE and os.path.exists(old_path):
        os.remove(old_path)

    # Lưu ảnh mới
    ext = os.path.splitext(file.filename)[1]
    new_filename = f"product_{int(time.time())}{ext}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], new_filename)
    file.save(save_path)
    save_image_name(new_filename)

    flash("Đổi ảnh sản phẩm thành công!")
    return redirect(url_for("index"))

# Trang QR
@app.route("/qr")
def qr_page():
    return render_template("qr.html")

# Sinh QR code
@app.route("/generate-qr", methods=["POST"])
def generate_qr():
    url = "https://thongtinsanphamUNI-com.onrender.com/"
    qr_img = qrcode.make(url)

    img_io = BytesIO()
    qr_img.save(img_io, "PNG")
    img_io.seek(0)
    return send_file(img_io, mimetype="image/png", as_attachment=True, download_name="qr.png")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)
