"""
    This file is part of Polichombr.

    (c) 2017 ANSSI-FR


    Description:
        Managers for all the actions associated with IDAPro models
"""

import datetime

from poli import app, db
from poli.models.idaactions import IDAAction, IDAActionSchema
from poli.models.idaactions import IDANameAction, IDACommentAction
from poli.models.idaactions import IDAStruct, IDAStructSchema
from poli.models.idaactions import IDAStructMember
from poli.models.idaactions import IDATypeAction
from poli.models.sample import Sample


class IDAActionsController(object):

    """
        Manage the recorded actions for IDA Pro.
    """
    @staticmethod
    def get_all(sid=None, timestamp=None):
        if sid is None:
            return False
        query = IDAAction.query
        query = query.filter(
            IDAAction.samples.any(Sample.id == sid))
        if timestamp is not None:
            query = query.filter(timestamp >= timestamp)
        schema = IDAActionSchema(many=True)
        return schema.dump(query.all()).data

    @staticmethod
    def add_comment(address, data):
        """
            Creates a new comment action
        """
        comment = IDACommentAction()
        comment.address = address
        comment.data = data
        comment.timestamp = datetime.datetime.now()
        db.session.add(comment)
        db.session.commit()
        return comment.id

    @staticmethod
    def filter_actions(action_type, sid, addr=None, timestamp=None):
        """
            Generate a filtered query for IDAActions,
            Filter by sample ID, address and timestamp
        """
        query = IDAAction.query.filter_by(type=action_type)
        query = query.filter(IDAAction.samples.any(Sample.id == sid))

        if addr is not None:
            query = query.filter_by(address=addr)

        if timestamp is not None:
            query = query.filter(IDAAction.timestamp > timestamp)

        return query.all()

    @classmethod
    def get_comments(cls, sid=None, addr=None, timestamp=None):
        """
            Filters for getting comments
            @arg addr Is there a comment for a specific address
            @timestamp Get only after this timestamp
        """
        data = cls.filter_actions('idacomment', sid, addr, timestamp)
        schema = IDAActionSchema(many=True)
        data = schema.dump(data).data
        return data

    @staticmethod
    def add_name(address=None, data=None):
        """
            Creates a new name action
        """
        name = IDANameAction()
        name.address = address
        name.data = data
        name.timestamp = datetime.datetime.now()
        db.session.add(name)
        db.session.commit()
        return name.id

    @classmethod
    def get_names(cls, sid, addr=None, timestamp=None):
        """
            Return defined names for a specific sample
            @arg addr the address for a specific name
            @timestamp Last desired timestamp
        """
        data = cls.filter_actions('idanames', sid, addr, timestamp)
        schema = IDAActionSchema(many=True)
        return schema.dump(data).data

    @staticmethod
    def create_struct(name=None):
        if name is None:
            app.logger.error("Cannot create anonymous struct")
            return False
        mstruct = IDAStruct()
        mstruct.name = name
        mstruct.data = name
        mstruct.timestamp = datetime.datetime.now()
        mstruct.size = 0
        db.session.add(mstruct)
        db.session.commit()
        return mstruct.id

    @staticmethod
    def get_structs(sid, timestamp=None):
        query = IDAStruct.query
        query = query.filter(IDAStruct.samples.any(Sample.id == sid))

        if timestamp is not None:
            query = query.filter(IDAStruct.timestamp > timestamp)

        data = query.all()
        schema = IDAStructSchema(many=True)
        return schema.dump(data).data

    @staticmethod
    def get_one_struct(struct_id):
        """
            Get only one structure
        """
        query = IDAStruct.query
        data = query.get(struct_id)

        schema = IDAStructSchema()
        return schema.dump(data).data

    @classmethod
    def get_struct_by_name(cls, sample_id, name):
        """
            Filter structs by sid, then by name
        """
        query = IDAStruct.query
        query = query.filter(IDAStruct.samples.any(Sample.id == sample_id))
        query = query.filter_by(name=name)
        data = query.first()

        schema = IDAStructSchema()
        return schema.dump(data).data

    @staticmethod
    def rename_struct(struct_id, name):
        """
            Update a struct's name and timestamp
        """
        mstruct = IDAStruct.query.get_or_404(struct_id)
        mstruct.name = name
        mstruct.timestamp = datetime.datetime.now()
        db.session.commit()
        return True

    @staticmethod
    def delete_struct(struct_id):
        """

        """
        mstruct = IDAStruct.query.get(struct_id)
        app.logger.debug("Deleting struct %s", mstruct.name)
        db.session.delete(mstruct)
        db.session.commit()
        return True

    @staticmethod
    def create_struct_member(name=None, size=None, offset=None):
        member = IDAStructMember()
        if member is None:
            return False
        member.name = name
        member.size = size
        member.offset = offset
        db.session.add(member)
        db.session.commit()
        return member.id

    @staticmethod
    def filter_member_id(struct_id, mid):
        """
        Utility to get a struct and a struct member from their ID
        """
        struct = IDAStruct.query.get(struct_id)
        member = IDAStructMember.query.get(mid)
        if struct is None or member is None:
            return None

        return struct, member

    @classmethod
    def add_member_to_struct(cls, struct_id=None, mid=None):
        """
            Add a new member at the member offset of the struct
        """
        struct, member = cls.filter_member_id(struct_id, mid)
        struct.members.append(member)
        # struct is updated, so we must update the timestamp
        struct.timestamp = datetime.datetime.now()
        if member.offset >= struct.size:
            struct.size += (member.offset - struct.size)
        struct.size += member.size
        db.session.commit()
        result = True
        return result

    @classmethod
    def change_struct_member_name(cls, struct_id, mid, new_name):
        """
            Rename a struct member, and update struct timestamp
        """
        struct, member = cls.filter_member_id(struct_id, mid)
        member.name = new_name
        struct.timestamp = datetime.datetime.now()
        db.session.commit()
        return True

    @classmethod
    def change_struct_member_size(cls, struct_id, mid, new_size):
        """
            Resize struct member
        """
        struct, member = cls.filter_member_id(struct_id, mid)

        if member.offset + member.size == struct.size:
            struct.size = struct.size - (member.size - new_size)
        member.size = new_size

        struct.timestamp = datetime.datetime.now()
        db.session.commit()

        return True

    @staticmethod
    def add_typedef(address, typedef):
        """
            Creates a new type definition
        """
        mtype = IDATypeAction()
        mtype.address = address
        mtype.data = typedef
        mtype.timestamp = datetime.datetime.now()
        db.session.add(mtype)
        db.session.commit()
        return mtype.id

    @classmethod
    def get_typedefs(cls, sid, addr=None, timestamp=None):
        """
            Return filtered IDA Pro type definitions
        """
        data = cls.filter_actions('idatypes', sid, addr, timestamp)
        schema = IDAActionSchema(many=True)
        return schema.dump(data).data
