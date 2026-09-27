try:
    from app.main import app
    print("App loaded successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
