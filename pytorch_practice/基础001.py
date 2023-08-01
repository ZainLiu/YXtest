import torch
from torch import nn
from torch.autograd import Variable
import six

a = torch.Tensor([3])
b = torch.Tensor([5])
x = Variable(a, requires_grad=True)
y = Variable(b, requires_grad=True)
z = 2 * x + y + 4
z.backward()
print(str(x.grad.data))
print(y.grad.data)

class linearRegression(nn.Module):
    def __init__(self):
        super(linearRegression, self).__init__()
        self.linear = nn.Linear(1, 1)  # input and output is 1 dimension

    def forward(self, x):
        out = self.linear(x)
        return out