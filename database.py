import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Create categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        icon TEXT DEFAULT '📌',
        color TEXT DEFAULT '#3B82F6',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create links table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        platform TEXT NOT NULL DEFAULT 'web',
        category_id INTEGER,
        tags TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        is_favorite INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    )
    """)

    # Create comments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        link_id INTEGER NOT NULL,
        author TEXT DEFAULT 'ฉัน',
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE
    )
    """)

    # Seed initial categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("ของกินโคราช", "🍜", "#F97316"),
            ("เที่ยวเขาใหญ่", "⛰️", "#10B981"),
            ("เที่ยวชลบุรี-ระยอง", "🏖️", "#06B6D4"),
            ("เที่ยวฟุกุโอกะ", "✈️", "#EC4899"),
            ("ที่พัก & คาเฟ่", "☕", "#8B5CF6"),
            ("ทั่วไป", "📌", "#6B7280"),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)",
            default_categories
        )

        # Retrieve IDs
        cat_map = {}
        for row in cursor.execute("SELECT id, name FROM categories").fetchall():
            cat_map[row["name"]] = row["id"]

        # Seed sample links
        sample_links = [
            (
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "10 ร้านเด็ดโคราช หมี่โคราชแท้ๆ และส้มตำรสแซ่บ",
                "รีวิวร้านอาหารเจ้าดังรอบเมืองโคราช แนะนำร้านข้างทางและร้านระดับตำนาน",
                "youtube",
                cat_map.get("ของกินโคราช"),
                "ของกิน, โคราช, ร้านเด็ด",
                "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600&auto=format&fit=crop&q=60",
                1
            ),
            (
                "https://www.tiktok.com/@khaoyai_guide/video/1234567890",
                "แจกแพลนเที่ยวเขาใหญ่ 2 วัน 1 คืน คาเฟ่เปิดใหม่เพียบ!",
                "จุดเช็คอินถ่ายรูปฟีลสวิสเซอร์แลนด์ สวนดอกไม้ และจุดชมวิวกังหันลม",
                "tiktok",
                cat_map.get("เที่ยวเขาใหญ่"),
                "เขาใหญ่, เที่ยวภูเขา, คาเฟ่",
                "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=600&auto=format&fit=crop&q=60",
                1
            ),
            (
                "https://www.facebook.com/RayongGuide/posts/987654321",
                "พิกัดซีฟู้ดสดๆ ชลบุรี-ระยอง กินริมหาดแม่รำพึงและบางแสน",
                "รวมร้านอาหารทะเลปูเป็นกุ้งเป็น น้ำจิ้มซีฟู้ดรสจัดจ้าน ราคาชาวบ้าน",
                "facebook",
                cat_map.get("เที่ยวชลบุรี-ระยอง"),
                "ชลบุรี, ระยอง, ซีฟู้ด, ทะเล",
                "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=600&auto=format&fit=crop&q=60",
                0
            ),
            (
                "https://www.youtube.com/watch?v=sampleFukuoka",
                "เที่ยวฟุกุโอกะ คิวชู 4 วัน 3 คืน ตะลุยกินฮากาตะราเมน & ศาลเจ้าดาไซฟุ",
                "พาเที่ยว Fukuoka, Hakata, Yatai street food และช้อปปิ้ง Canal City",
                "youtube",
                cat_map.get("เที่ยวฟุกุโอกะ"),
                "ญี่ปุ่น, ฟุกุโอกะ, ราเมน",
                "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=600&auto=format&fit=crop&q=60",
                1
            )
        ]

        cursor.executemany("""
        INSERT INTO links (url, title, description, platform, category_id, tags, image_url, is_favorite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_links)

        # Get link IDs and add initial comments
        links = cursor.execute("SELECT id, title FROM links").fetchall()
        sample_comments = [
            (links[0]["id"], "ฉัน", "ร้านหมี่โคราชร้านที่ 3 ในคลิปต้องไปลอง เส้นเหนียวนุ่มมาก"),
            (links[0]["id"], "ฉัน", "เปิด 09:30 - 16:00 น. ไปช่วงเที่ยงคนแน่นหน่อย"),
            (links[1]["id"], "ฉัน", "คาเฟ่สีขาวมุมถ่ายรูปสวย แนะนำไปเช้าๆ แสงสวย ไม่ร้อน"),
            (links[2]["id"], "ฉัน", "ร้านปูเป็นอยู่ใกล้หาด บรรยากาศดีตอนพระอาทิตย์ตกดิน"),
            (links[3]["id"], "ฉัน", "พาสรถไฟใต้ดินซื้อที่สนามบินฟุกุโอกะได้เลย เดินทางง่ายมาก"),
        ]
        cursor.executemany("""
        INSERT INTO comments (link_id, author, content)
        VALUES (?, ?, ?)
        """, sample_comments)

    conn.commit()
    conn.close()

# Category operations
def get_categories_with_counts() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, COUNT(l.id) as link_count
        FROM categories c
        LEFT JOIN links l ON l.category_id = c.id
        GROUP BY c.id
        ORDER BY c.id ASC
    """)
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

def create_category(name: str, icon: str = "📌", color: str = "#3B82F6") -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO categories (name, icon, color) VALUES (?, ?, ?)",
        (name.strip(), icon.strip(), color.strip())
    )
    cat_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT *, 0 as link_count FROM categories WHERE id = ?", (cat_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row

def delete_category(category_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()

# Link operations
def get_links(
    category_id: Optional[int] = None,
    platform: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            l.*, 
            c.name as category_name, 
            c.icon as category_icon, 
            c.color as category_color,
            COUNT(cm.id) as comment_count
        FROM links l
        LEFT JOIN categories c ON l.category_id = c.id
        LEFT JOIN comments cm ON cm.link_id = l.id
        WHERE 1=1
    """
    params = []

    if category_id is not None:
        query += " AND l.category_id = ?"
        params.append(category_id)

    if platform and platform != "all":
        query += " AND l.platform = ?"
        params.append(platform.lower())

    if is_favorite is not None and is_favorite:
        query += " AND l.is_favorite = 1"

    if search:
        search_param = f"%{search.strip()}%"
        query += """ AND (
            l.title LIKE ? OR 
            l.url LIKE ? OR 
            l.description LIKE ? OR 
            l.tags LIKE ? OR 
            c.name LIKE ?
        )"""
        params.extend([search_param] * 5)

    query += " GROUP BY l.id ORDER BY l.is_favorite DESC, l.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    links = [dict(row) for row in rows]
    conn.close()
    return links

def get_link_by_id(link_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, c.name as category_name, c.icon as category_icon, c.color as category_color
        FROM links l
        LEFT JOIN categories c ON l.category_id = c.id
        WHERE l.id = ?
    """, (link_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_link(
    url: str,
    title: str,
    description: str = "",
    platform: str = "web",
    category_id: Optional[int] = None,
    tags: str = "",
    image_url: str = "",
    is_favorite: int = 0
) -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO links (url, title, description, platform, category_id, tags, image_url, is_favorite)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (url.strip(), title.strip(), description.strip(), platform.lower(), category_id, tags.strip(), image_url.strip(), is_favorite))
    link_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_link_by_id(link_id)

def update_link(
    link_id: int,
    url: str,
    title: str,
    description: str = "",
    platform: str = "web",
    category_id: Optional[int] = None,
    tags: str = "",
    image_url: str = "",
    is_favorite: int = 0
) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE links
        SET url = ?, title = ?, description = ?, platform = ?, category_id = ?, tags = ?, image_url = ?, is_favorite = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (url.strip(), title.strip(), description.strip(), platform.lower(), category_id, tags.strip(), image_url.strip(), is_favorite, link_id))
    conn.commit()
    conn.close()
    return get_link_by_id(link_id)

def toggle_favorite(link_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE links SET is_favorite = 1 - is_favorite WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    return get_link_by_id(link_id)

def delete_link(link_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()

# Comment operations
def get_comments(link_id: int) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM comments WHERE link_id = ? ORDER BY created_at ASC", (link_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_comment(link_id: int, content: str, author: str = "ฉัน") -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (link_id, author, content) VALUES (?, ?, ?)",
        (link_id, author.strip(), content.strip())
    )
    comment_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row

def delete_comment(comment_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    conn.commit()
    conn.close()

# Export & Import for backup / migration
def export_all_data() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    categories = [dict(r) for r in cursor.execute("SELECT * FROM categories").fetchall()]
    links = [dict(r) for r in cursor.execute("SELECT * FROM links").fetchall()]
    comments = [dict(r) for r in cursor.execute("SELECT * FROM comments").fetchall()]
    conn.close()
    return {
        "version": 1,
        "exported_at": datetime.now().isoformat(),
        "categories": categories,
        "links": links,
        "comments": comments
    }

def import_all_data(data: Dict[str, Any]):
    conn = get_db()
    cursor = conn.cursor()
    
    if "categories" in data:
        for cat in data["categories"]:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (id, name, icon, color)
                VALUES (?, ?, ?, ?)
            """, (cat.get("id"), cat.get("name"), cat.get("icon", "📌"), cat.get("color", "#3B82F6")))

    if "links" in data:
        for l in data["links"]:
            cursor.execute("""
                INSERT OR REPLACE INTO links (id, url, title, description, platform, category_id, tags, image_url, is_favorite, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                l.get("id"), l.get("url"), l.get("title"), l.get("description", ""),
                l.get("platform", "web"), l.get("category_id"), l.get("tags", ""),
                l.get("image_url", ""), l.get("is_favorite", 0),
                l.get("created_at", datetime.now().isoformat()),
                l.get("updated_at", datetime.now().isoformat())
            ))

    if "comments" in data:
        for c in data["comments"]:
            cursor.execute("""
                INSERT OR REPLACE INTO comments (id, link_id, author, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                c.get("id"), c.get("link_id"), c.get("author", "ฉัน"),
                c.get("content"), c.get("created_at", datetime.now().isoformat())
            ))

    conn.commit()
    conn.close()
