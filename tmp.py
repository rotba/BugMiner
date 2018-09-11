class Point:

    def __init__(self,x,y):
        """ Create a new point at the origin """
        self.x = x
        self.y = y
    def __eq__(self, other):
        """ Create a new point at the origin """
        return False
        return self.x==other.x and self.y==other.y
list_1 = [1,2,3]
print(1 in list_1)
print(4 in list_1)
p =Point(1,2)
list_2 = [p,Point(3,4)]
print(Point(1,2) in list_2)