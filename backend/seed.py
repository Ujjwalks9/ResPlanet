import asyncio
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy import select

# Ensure this runs from the /backend directory
from app.database import AsyncSessionLocal
from app.models import User, Project, ProjectFile, CollabRequest, ChatMessage

fake = Faker()

# A tiny valid PDF binary (Blank Page) so the "View PDF" feature doesn't crash
DUMMY_PDF_DATA = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources << >>\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 21\n>>\nstream\nBT\n/F1 24 Tf\n100 700 Td\n(Fake Research Paper) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000060 00000 n\n0000000117 00000 n\n0000000224 00000 n\ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n300\n%%EOF"

TECH_TOPICS = ["AI", "Generative AI", "Blockchain", "Quantum Computing", "React", "Neural Networks", "Cybersecurity", "IoT", "Cloud Architecture", "Robotics"]

async def seed_data():
    print("🌱 Starting Database Seed...")
    
    async with AsyncSessionLocal() as db:
        
        # 1. Create Fake Users
        print("👤 Creating 10 Fake Users...")
        users = []
        for _ in range(10):
            uid = f"user_{uuid.uuid4().hex[:8]}"
            user = User(
                id=uid,
                email=fake.unique.email(),
                name=fake.name(),
                picture=f"https://api.dicebear.com/7.x/avataaars/svg?seed={uid}" # Random avatar image
            )
            db.add(user)
            users.append(user)
        
        await db.commit()

        # 2. Create Projects & Files
        print("📄 Creating 20 Research Projects...")
        projects = []
        for _ in range(20):
            owner = random.choice(users)
            title = fake.catch_phrase() + " in " + random.choice(TECH_TOPICS)
            
            project = Project(
                id=uuid.uuid4(),
                user_id=owner.id,
                title=title,
                abstract=fake.paragraph(nb_sentences=8),
                topics=random.sample(TECH_TOPICS, k=3),
                created_at=fake.date_time_between(start_date="-1y", end_date="now"),
                views_count=random.randint(50, 5000), # Random high views for "Trending"
                is_processed=True
            )
            db.add(project)
            projects.append(project)

            # Add Dummy PDF File
            p_file = ProjectFile(
                id=uuid.uuid4(),
                project_id=project.id,
                filename=f"{title.replace(' ', '_')[:20]}.pdf",
                content_type="application/pdf",
                data=DUMMY_PDF_DATA
            )
            db.add(p_file)

        await db.commit()

        # 3. Create Collab Requests
        print("🤝 Simulating Collaborations...")
        accepted_collabs = []
        
        for proj in projects:
            if random.random() > 0.4: # 60% chance of having requests
                sender = random.choice([u for u in users if u.id != proj.user_id])
                status = random.choice(["PENDING", "ACCEPTED", "REJECTED"])
                
                req = CollabRequest(
                    sender_id=sender.id,
                    receiver_id=proj.user_id,
                    project_id=proj.id,
                    status=status
                )
                db.add(req)
                
                if status == "ACCEPTED":
                    accepted_collabs.append((proj, sender, proj.user))

        await db.commit()

        # 4. Create Chat Messages
        print("💬 Generating Chat History...")
        for proj, collaborator, owner in accepted_collabs:
            # Generate a conversation
            for _ in range(random.randint(2, 6)):
                sender = random.choice([collaborator, owner])
                msg = ChatMessage(
                    project_id=proj.id,
                    sender_id=sender.id,
                    content=fake.sentence(),
                    is_ai=False,
                    created_at=datetime.utcnow()
                )
                db.add(msg)
            
            # Add an AI message occasionally
            if random.random() > 0.5:
                db.add(ChatMessage(
                    project_id=proj.id,
                    sender_id=owner.id, 
                    content=f"Based on the analysis of '{proj.title}', the methodology appears sound...",
                    is_ai=True,
                    created_at=datetime.utcnow()
                ))

        await db.commit()
        print("🎉 SEEDING COMPLETE! Your app is now populated.")

if __name__ == "__main__":
    asyncio.run(seed_data())