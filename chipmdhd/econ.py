from . import DEFAULT_MODELING_YEAR, DEFAULT_INFLATION_RATE

class Dollar(object):
    default_baseyear = DEFAULT_MODELING_YEAR
    inflation_rate = DEFAULT_INFLATION_RATE
    
    @property
    def rate(self):
        return 1 + self.inflation_rate

    def __init__(self, amount=0.0, dollaryear=default_baseyear):
        self.amount = amount
        self.baseyear = dollaryear
    
    def asyr(self, year):
        amount = self.amount * self.rate**(year - self.baseyear)
        return self.__class__(amount, year)
    
    @property
    def default_yr_amount(self):
        return self.asyr(self.default_baseyear).amount
    
    def __add__(self, other):
        new_amount = self.default_yr_amount + other.default_yr_amount
        return self.__class__(new_amount).asyr(self.baseyear)
    
    def __sub__(self, other):
        new_amount = self.default_yr_amount - other.default_yr_amount
        return self.__class__(new_amount).asyr(self.baseyear)
    
    def __mul__(self, other):
        new_amount = self.default_yr_amount * other
        return self.__class__(new_amount).asyr(self.baseyear)
    
    def __rmul__(self, other):
        new_amount = self.default_yr_amount * other
        return self.__class__(new_amount).asyr(self.baseyear)
    
    def __truediv__(self, other):
        new_amount = self.default_yr_amount / other
        return self.__class__(new_amount).asyr(self.baseyear)
    
    def __repr__(self):
        return f'{self.amount:.2f} (${self.baseyear})'