import shutil
import os
from datetime import datetime

def auto_backup():

    os.makedirs("data/backups", exist_ok=True)

    if os.path.exists("data/simogramme.db"):

        name = datetime.now().strftime("%Y%m%d_%H%M%S")

        shutil.copy(
            "data/simogramme.db",
            f"data/backups/simogramme_{name}.db"
        )
