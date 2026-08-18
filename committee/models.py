from django.db import models

import os
import hashlib
from io import BytesIO
from PIL import Image

from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.deconstruct import deconstructible
from django.core.files.base import ContentFile

from conference.models import QuARCConference

@deconstructible
class committee_photo_path(object):
    def __init__(self, subdir):
        self.subdir = subdir

    def __call__(self, instance, filename):
        # Anonymize filenames (presenter is unique on (last_name, first_name) pair)
        _, ext = os.path.splitext(filename)
        # md5 hex digest is 128 bits, so should be 32 chars long
        name = (instance.email).encode('utf-8')
        filename = 'committee_' + hashlib.md5(name).hexdigest()
        # Django's storage class is cutting of full filename and appending its own random
        # chars at the end. This behavior is acceptable, but makes it a bit harder to use
        # above technique to locate a file based on instance first/last_name alone.
        return os.path.join(self.subdir, filename + ext)

class CommitteeMember(models.Model):
    first_name = models.CharField(max_length=32, blank=True)
    last_name = models.CharField(max_length=32, blank=False)
    email = models.EmailField(blank=False, unique=True)
    status = models.CharField(max_length=32, blank=True)
    group = models.CharField(max_length=64, blank=True)
    profile_image = models.ImageField(upload_to=committee_photo_path('committee_photos'), blank=True)
    profile_image_thumb = models.ImageField(upload_to=committee_photo_path('thumbs'),
                                            blank=True, editable=False)

    def save(self):
        # Add thumbnail (if provided)
        force_update = False
        if self.profile_image:
            max_size = (300,600)
            #Original photo
            imgFile = Image.open(self.profile_image)
            #Convert to RGB
            if imgFile.mode not in ('L', 'RGB'):
                imgFile = imgFile.convert('RGB')
            #Save thumbnail
            working = imgFile.copy()
            working.thumbnail(max_size,Image.LANCZOS)
            fp = BytesIO()
            working.save(fp, 'JPEG', quality=95)
            working.seek(0)
            cf = ContentFile(fp.getvalue())
            name, _ = os.path.splitext(self.profile_image.name)
            self.profile_image_thumb.save(name=name + '.jpg',content=cf,save=False)
            if self.id:
                force_update = True # Maintain DB integrity
        super(CommitteeMember, self).save(force_update=force_update)

    def __str__(self):
        return '%s, %s'%(self.last_name, self.first_name)

class CommitteeRole(models.Model):
    class RoleType(models.IntegerChoices):
        Committee = 0
        Design = 1
        Logistics = 2
        Social = 3
        Programming = 4
        Swag = 5
        Photography = 6
        Web = 7

    role_type = models.IntegerField(choices=RoleType.choices)
    role_conference = models.ForeignKey(QuARCConference, on_delete=models.CASCADE)
    member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['role_type']

    def __str__(self):
        return '%d %s Chair, %s %s'%(self.role_conference.year, self.get_role_type_display(),
                                     self.member.first_name, self.member.last_name)
