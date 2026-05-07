from server.routes import app
import os

# ================= START SERVER =================
if __name__ == "__main__":

    print("Server running...")

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
