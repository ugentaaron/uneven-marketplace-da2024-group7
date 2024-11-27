class Config: 
    SECRET_KEY = 'FEZ_agb.mcb4rvb.xyz'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres.dqmrenandyxqtmhkvfyu:Wtf8fGrMl3pFUJyq@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    UPLOAD_FOLDER = 'app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Optioneel: max 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} 

