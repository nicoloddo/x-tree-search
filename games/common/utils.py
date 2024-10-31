class AutoCallDict(dict):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if callable(value):
            return value()
        return value
        
    def items(self):
        return [(key, self[key]) for key in self]
    
    def values(self):
        return [self[key] for key in self]