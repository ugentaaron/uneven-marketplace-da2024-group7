class Config:
    SECRET_KEY = 'FEZ_agb.mcb4rvb.xyz'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.dqmrenandyxqtmhkvfyu:Wtf8fGrMl3pFUJyq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Supabase configuration
    SUPABASE_URL = 'https://dqmrenandyxqtmhkvfyu.supabase.co'
    SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxbXJlbmFuZHl4cXRtaGt2Znl1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA4ODc1MDcsImV4cCI6MjA0NjQ2MzUwN30.v6b4I70suTdOElf6P0hfsbcbC96NXlQhtnZdKPt4SeU'
    SUPABASE_BUCKET = 'vehicle_photos'

    UPLOAD_FOLDER = 'app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Optional: max 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}