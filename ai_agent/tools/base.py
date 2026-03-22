class BaseTool:
    name = "base"
    description = "Base tool"

    def run(self, **kwargs):
        raise NotImplementedError
