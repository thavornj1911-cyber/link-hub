import os
import re
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import database

# Initialize database
database.init_db()

app = FastAPI(title="LinkHub - Web App สำหรับจัดเก็บและคอมเมนต์ลิ้งค์")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Helper: Detect platform
def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "tiktok.com" in url_lower:
        return "tiktok"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return "facebook"
    elif "instagram.com" in url_lower:
        return "instagram"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "x"
    elif "lemon8-app.com" in url_lower or "lemon8" in url_lower:
        return "lemon8"
    elif "threads.net" in url_lower:
        return "threads"
    elif "google.com/maps" in url_lower or "maps.app.goo.gl" in url_lower or "goo.gl/maps" in url_lower:
        return "maps"
    return "web"

# Helper: Extract YouTube ID
def extract_youtube_id(url: str) -> Optional[str]:
    m = re.search(r'(?:v=|\/|youtu\.be\/|embed\/)([0-9A-Za-z_-]{11})', url)
    return m.group(1) if m else None

# Helper: HTML parser for OpenGraph and title tags
class MetaTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.description = ""
        self.image = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag_lower = tag.lower()
        
        if tag_lower == "title" and not self.title:
            self._in_title = True
            
        if tag_lower == "meta":
            prop = attrs_dict.get("property", "").lower()
            name = attrs_dict.get("name", "").lower()
            content = attrs_dict.get("content", "")

            if (prop == "og:title" or name == "twitter:title") and not self.title:
                self.title = content
            elif (prop == "og:description" or name == "description" or name == "twitter:description") and not self.description:
                self.description = content
            elif (prop == "og:image" or name == "twitter:image") and not self.image:
                self.image = content

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()

# Pydantic Schemas
class LinkCreate(BaseModel):
    url: str
    title: str
    description: Optional[str] = ""
    platform: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[str] = ""
    image_url: Optional[str] = ""
    is_favorite: Optional[int] = 0
    initial_comment: Optional[str] = None

class LinkUpdate(BaseModel):
    url: str
    title: str
    description: Optional[str] = ""
    platform: Optional[str] = "web"
    category_id: Optional[int] = None
    tags: Optional[str] = ""
    image_url: Optional[str] = ""
    is_favorite: Optional[int] = 0

class CategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = "📌"
    color: Optional[str] = "#3B82F6"

class CommentCreate(BaseModel):
    content: str
    author: Optional[str] = "ฉัน"

class FetchMetaRequest(BaseModel):
    url: str

# API Routes
@app.get("/api/categories")
def get_categories():
    return database.get_categories_with_counts()

@app.post("/api/categories")
def create_category(payload: CategoryCreate):
    try:
        cat = database.create_category(payload.name, payload.icon or "📌", payload.color or "#3B82F6")
        return cat
    except Exception as e:
        raise HTTPException(status_code=400, detail="ชื่อหมวดหมู่นี้มีอยู่แล้ว หรือข้อมูลไม่ถูกต้อง")

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int):
    database.delete_category(category_id)
    return {"message": "Category deleted"}

@app.get("/api/links")
def list_links(
    category_id: Optional[int] = Query(None),
    platform: Optional[str] = Query(None),
    is_favorite: Optional[bool] = Query(None),
    search: Optional[str] = Query(None)
):
    return database.get_links(category_id, platform, is_favorite, search)

@app.get("/api/links/{link_id}")
def get_link(link_id: int):
    link = database.get_link_by_id(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    comments = database.get_comments(link_id)
    link["comments"] = comments
    return link

@app.post("/api/links")
def add_link(payload: LinkCreate):
    platform = payload.platform or detect_platform(payload.url)
    image_url = payload.image_url or ""
    
    # Auto-thumbnail for YouTube if none provided
    if platform == "youtube" and not image_url:
        yt_id = extract_youtube_id(payload.url)
        if yt_id:
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"

    link = database.create_link(
        url=payload.url,
        title=payload.title,
        description=payload.description or "",
        platform=platform,
        category_id=payload.category_id,
        tags=payload.tags or "",
        image_url=image_url,
        is_favorite=payload.is_favorite or 0
    )

    if payload.initial_comment and payload.initial_comment.strip():
        database.add_comment(link["id"], payload.initial_comment.strip(), author="ฉัน")

    link["comments"] = database.get_comments(link["id"])
    return link

@app.put("/api/links/{link_id}")
def update_link(link_id: int, payload: LinkUpdate):
    platform = payload.platform or detect_platform(payload.url)
    image_url = payload.image_url or ""
    if platform == "youtube" and not image_url:
        yt_id = extract_youtube_id(payload.url)
        if yt_id:
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"

    link = database.update_link(
        link_id=link_id,
        url=payload.url,
        title=payload.title,
        description=payload.description or "",
        platform=platform,
        category_id=payload.category_id,
        tags=payload.tags or "",
        image_url=image_url,
        is_favorite=payload.is_favorite or 0
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.post("/api/links/{link_id}/toggle-favorite")
def toggle_favorite(link_id: int):
    link = database.toggle_favorite(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@app.delete("/api/links/{link_id}")
def delete_link(link_id: int):
    database.delete_link(link_id)
    return {"message": "Link deleted"}

# Comments
@app.get("/api/links/{link_id}/comments")
def get_comments(link_id: int):
    return database.get_comments(link_id)

@app.post("/api/links/{link_id}/comments")
def add_comment(link_id: int, payload: CommentCreate):
    link = database.get_link_by_id(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    comment = database.add_comment(link_id, payload.content, payload.author or "ฉัน")
    return comment

@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int):
    database.delete_comment(comment_id)
    return {"message": "Comment deleted"}

# URL Metadata Scraper
@app.post("/api/links/fetch-meta")
def fetch_meta(payload: FetchMetaRequest):
    url = payload.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    platform = detect_platform(url)
    title = ""
    description = ""
    image_url = ""

    # YouTube quick metadata
    if platform == "youtube":
        yt_id = extract_youtube_id(url)
        if yt_id:
            image_url = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg"

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type:
                # Read first 128KB
                html_bytes = response.read(131072)
                charset = response.headers.get_content_charset() or "utf-8"
                html_text = html_bytes.decode(charset, errors="ignore")
                parser = MetaTagParser()
                parser.feed(html_text)
                title = parser.title or ""
                description = parser.description or ""
                if not image_url and parser.image:
                    image_url = parser.image
    except Exception:
        pass

    return {
        "url": url,
        "platform": platform,
        "title": title or "",
        "description": description or "",
        "image_url": image_url or ""
    }

# Export and Import
@app.get("/api/export")
def export_data():
    return database.export_all_data()

@app.post("/api/import")
async def import_data(request: Request):
    try:
        data = await request.json()
        database.import_all_data(data)
        return {"message": "Data imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "app": "LinkHub"}

# Frontend SPA
@app.get("/")
def index():
    html_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file):
        return FileResponse(html_file, media_type="text/html")
    return HTMLResponse("<h1>LinkHub Loading...</h1>")

# Mount static folder if exists
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
