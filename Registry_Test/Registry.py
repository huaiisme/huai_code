class Registry:
    def __init__(self, name: str):
        self.name = name
        self._module_dict = dict()

    def register(self, module_name: str, module):
        self._module_dict[module_name] = module

    def get(self, module_name: str):
        # 调用字典自带的get方法，根据key返回value
        return self._module_dict.get(module_name)



BACKBONES = Registry('backbone')

class ResNet:
    def __init__(self, depth=50):
        self.depth = depth


BACKBONES.register('ResNet', ResNet)
resnet_class = BACKBONES.get('ResNet')

model = resnet_class(depth=101)

print(model.depth)

