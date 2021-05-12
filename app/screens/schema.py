from marshmallow import fields, Schema


class MediaSchema(Schema):
    """MediaSchema"""
    duration = fields.Number(attribute="duration")
    media_type = fields.String(attribute="media_type")
    location = fields.String(attribute="location")

class PlaylistSchema(Schema):
    playlist = fields.List(fields.Nested(MediaSchema), attribute="playlist")
    
