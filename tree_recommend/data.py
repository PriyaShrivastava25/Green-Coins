import json
import os

def load_tree_data():
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'tree_recommendations.json')

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

if __name__ == "__main__":
    print(load_tree_data())
