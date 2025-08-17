from app import app

if __name__ == "__main__":
    # Render'ın verdiği PORT değişkenini oku, yoksa 5000 kullan
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
