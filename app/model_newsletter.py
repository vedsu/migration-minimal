from app import mongo


def normalize_website(website):
    if not website:
        return None

    return str(website).upper().strip()


class Newsletter:

    # this is for masterdatabackend
    @staticmethod
    def count_newsletter(website=None):
        try:
            website = normalize_website(website)

            query = {}

            if website:
                query["website"] = website

            return list(mongo.db.newsletter_data.find(query))

        except Exception:
            return []

    # this is for masterdatabackend
    @staticmethod
    def list_newsletter(website=None):
        newsletter_list = []

        try:
            website = normalize_website(website)

            query = {}

            if website:
                query["website"] = website

            newsletter_data = list(
                mongo.db.newsletter_data.find(query).sort("published_date", 1)
            )

            for newsletter in newsletter_data:
                newsletter_dict = {
                    "id": newsletter.get("id"),
                    "topic": newsletter.get("topic"),
                    "category": newsletter.get("category"),
                    "description": newsletter.get("description"),
                    "website": newsletter.get("website"),
                    "price": newsletter.get("price"),
                    "thumbnail": newsletter.get("thumbnail"),
                    "document": newsletter.get("document"),
                    "published_at": newsletter.get("published_date")
                }

                newsletter_list.append(newsletter_dict)

        except Exception as e:
            newsletter_list = [str(e)]

        return newsletter_list

    # this is for masterbackend
    @staticmethod
    def create_newsletter(newsletter):
        try:
            if "website" in newsletter:
                newsletter["website"] = normalize_website(newsletter.get("website"))

            mongo.db.newsletter_data.insert_one(newsletter)

            return {
                "success": True,
                "message": "newsletter added successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }

    # this is for website backend
    @staticmethod
    def activelist_newsletter(website=None):
        newsletter_list = []

        try:
            website = normalize_website(website)

            query = {
                "status": "Active"
            }

            if website:
                query["website"] = website

            newsletter_data = list(
                mongo.db.newsletter_data.find(query).sort("published_date", -1)
            )

            for newsletter in newsletter_data:
                newsletter_dict = {
                    "id": newsletter.get("id"),
                    "topic": newsletter.get("topic"),
                    "category": newsletter.get("category"),
                    "description": newsletter.get("description"),
                    "website": newsletter.get("website"),
                    "price": newsletter.get("price"),
                    "thumbnail": newsletter.get("thumbnail"),
                    "document": newsletter.get("document"),
                    "published_at": newsletter.get("published_date")
                }

                newsletter_list.append(newsletter_dict)

        except Exception as e:
            newsletter_list = [str(e)]

        return newsletter_list

    @staticmethod
    def view_newsletter(n_id, website=None):
        newsletter_info = None

        try:
            website = normalize_website(website)

            query = {
                "id": n_id
            }

            if website:
                query["website"] = website

            newsletter = mongo.db.newsletter_data.find_one(query)

            if not newsletter:
                return None

            newsletter_info = {
                "id": newsletter.get("id"),
                "topic": newsletter.get("topic"),
                "category": newsletter.get("category"),
                "description": newsletter.get("description"),
                "website": newsletter.get("website"),
                "price": newsletter.get("price"),
                "thumbnail": newsletter.get("thumbnail"),
                "document": newsletter.get("document"),
                "published_at": newsletter.get("published_date")
            }

        except Exception:
            newsletter_info = None

        return newsletter_info

    @staticmethod
    def edit_newsletter(n_id, newsletter_status, website=None):
        try:
            website = normalize_website(website)

            query = {
                "id": n_id
            }

            if website:
                query["website"] = website

            mongo.db.newsletter_data.update_one(
                query,
                {
                    "$set": {
                        "status": newsletter_status
                    }
                }
            )

            return {
                "success": True,
                "message": "status update successfull"
            }

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }
