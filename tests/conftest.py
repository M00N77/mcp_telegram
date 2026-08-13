import sys
import os

# Добавляем папку src в PYTHONPATH для тестов
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
