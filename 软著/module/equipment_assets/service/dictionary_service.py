from models import IsDelete
from models.dictionary import Dictionary, DictionaryType


class DictionaryService:

    def get_top_parent_ids(self, dictionary_set):
        """传入子类词条set，返回父类词条id列表"""
        parent_id_list = []
        for dictionary in dictionary_set:
            if dictionary.type == DictionaryType.Parent:
                parent_id_list.append(dictionary.id)
            else:
                parent_id = self.__get_top_parent(dictionary)
                parent_id_list.append(parent_id)
        return parent_id_list

    def __get_top_parent(self, son_dictionary):
        """递归查找父类词条id"""
        query_list = [Dictionary.id == son_dictionary.parent_id]
        parent_dictionary = Dictionary.query.filter(*query_list).first()
        if not parent_dictionary and son_dictionary.type == DictionaryType.Son:
            raise Exception(f'找不到父级词条，并且当前也不为父类词条，属于脏数据,id:{son_dictionary.id}')
        if parent_dictionary.type == DictionaryType.Parent:
            return parent_dictionary.id
        else:
            return self.__get_top_parent(parent_dictionary)

    def delete_children(self, dictionary_id):
        """递归删除所有后代词条"""
        son_dictionary_set = Dictionary.query.filter_by(parent_id=dictionary_id, is_delete=IsDelete.NORMAL,
                                                        type=DictionaryType.Son).all()
        if not son_dictionary_set:
            return
        for son_dictionary in son_dictionary_set:
            son_dictionary.is_delete = IsDelete.Deleted
            self.delete_children(son_dictionary.id)
