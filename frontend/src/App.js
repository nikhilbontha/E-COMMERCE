import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Toast } from './components/ui/toast';
import { Avatar, AvatarFallback, AvatarImage } from './components/ui/avatar';
import { Separator } from './components/ui/separator';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (savedUser && token) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, [token]);

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { token: newToken, user: userData } = response.data;
      
      localStorage.setItem('token', newToken);
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(newToken);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (name, email, password, phone = '') => {
    try {
      const response = await axios.post(`${API}/auth/register`, { name, email, password, phone });
      const { token: newToken, user: userData } = response.data;
      
      localStorage.setItem('token', newToken);
      localStorage.setItem('user', JSON.stringify(userData));
      setToken(newToken);
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();
  const [showAuthDialog, setShowAuthDialog] = useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between px-6">
        <Link to="/" className="flex items-center space-x-2">
          <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
            <span className="text-white font-bold text-sm">EM</span>
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            ElectroMart
          </span>
        </Link>

        <nav className="hidden md:flex items-center space-x-6">
          <Link to="/" className="text-sm font-medium hover:text-blue-600 transition-colors">Home</Link>
          <Link to="/products" className="text-sm font-medium hover:text-blue-600 transition-colors">Products</Link>
          <Link to="/categories" className="text-sm font-medium hover:text-blue-600 transition-colors">Categories</Link>
        </nav>

        <div className="flex items-center space-x-4">
          {user ? (
            <div className="flex items-center space-x-4">
              <Link to="/loyalty" className="flex items-center space-x-2 text-sm">
                <Badge variant="secondary" className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black">
                  {user.loyalty_points} pts
                </Badge>
                <Badge variant="outline" className="capitalize">
                  {user.loyalty_tier}
                </Badge>
              </Link>
              <Avatar className="h-8 w-8">
                <AvatarImage src="" />
                <AvatarFallback>{user.name?.[0]?.toUpperCase()}</AvatarFallback>
              </Avatar>
              <Button variant="outline" size="sm" onClick={logout}>Logout</Button>
            </div>
          ) : (
            <Dialog open={showAuthDialog} onOpenChange={setShowAuthDialog}>
              <DialogTrigger asChild>
                <Button>Sign In</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Welcome to ElectroMart</DialogTitle>
                  <DialogDescription>
                    Join our loyalty program and earn rewards on every purchase!
                  </DialogDescription>
                </DialogHeader>
                <AuthTabs onSuccess={() => setShowAuthDialog(false)} />
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>
    </header>
  );
};

// Auth Tabs Component
const AuthTabs = ({ onSuccess }) => {
  const { login, register } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const formData = new FormData(e.target);
    const email = formData.get('email');
    const password = formData.get('password');
    
    const result = await login(email, password);
    
    if (result.success) {
      onSuccess();
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const formData = new FormData(e.target);
    const name = formData.get('name');
    const email = formData.get('email');
    const password = formData.get('password');
    const phone = formData.get('phone');
    
    const result = await register(name, email, password, phone);
    
    if (result.success) {
      onSuccess();
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <Tabs defaultValue="login" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="login">Login</TabsTrigger>
        <TabsTrigger value="register">Register</TabsTrigger>
      </TabsList>
      
      <TabsContent value="login">
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" name="email" type="email" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" name="password" type="password" required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </TabsContent>
      
      <TabsContent value="register">
        <form onSubmit={handleRegister} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" name="name" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" name="email" type="email" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="phone">Phone (Optional)</Label>
            <Input id="phone" name="phone" type="tel" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" name="password" type="password" required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Creating account...' : 'Create Account'}
          </Button>
          <div className="text-xs text-gray-500 text-center">
            Get 100 welcome points when you sign up! 🎉
          </div>
        </form>
      </TabsContent>
    </Tabs>
  );
};

// Home Page
const HomePage = () => {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, categoriesRes] = await Promise.all([
          axios.get(`${API}/products?limit=6`),
          axios.get(`${API}/categories`)
        ]);
        
        setFeaturedProducts(productsRes.data);
        setCategories(categoriesRes.data);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-[70vh] flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-900/90 to-purple-900/90 z-10"></div>
        <img 
          src="https://images.unsplash.com/photo-1498049794561-7780e7231661" 
          alt="Hero background"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="relative z-20 text-center text-white max-w-4xl px-6">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
            Premium Electronics
            <span className="block bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
              Rewards Included
            </span>
          </h1>
          <p className="text-xl mb-8 opacity-90">
            Discover the latest gadgets and earn loyalty points with every purchase
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700">
              Shop Now
            </Button>
            <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-black">
              Join Loyalty Program
            </Button>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-16 px-6">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Shop by Category</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {categories.map((category) => (
              <Card key={category.id} className="group cursor-pointer hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
                <CardContent className="p-6">
                  <img 
                    src={category.image_url || "https://images.unsplash.com/photo-1498049794561-7780e7231661"} 
                    alt={category.name}
                    className="w-full h-40 object-cover rounded-lg mb-4 group-hover:scale-105 transition-transform"
                  />
                  <h3 className="text-xl font-semibold mb-2">{category.name}</h3>
                  <p className="text-gray-600 text-sm">{category.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="container mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Featured Products</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featuredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </section>

      {/* Loyalty Program CTA */}
      <section className="py-16 px-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto text-center">
          <h2 className="text-4xl font-bold mb-6">Join Our Loyalty Program</h2>
          <p className="text-xl mb-8 opacity-90">
            Earn points with every purchase and unlock exclusive rewards
          </p>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="text-center">
              <Badge className="text-lg px-4 py-2 bg-yellow-500 text-black">Bronze</Badge>
              <p className="mt-2">5% Discount</p>
            </div>
            <div className="text-center">
              <Badge className="text-lg px-4 py-2 bg-gray-400 text-black">Silver</Badge>
              <p className="mt-2">10% + Free Shipping</p>
            </div>
            <div className="text-center">
              <Badge className="text-lg px-4 py-2 bg-yellow-400 text-black">Gold</Badge>
              <p className="mt-2">15% + Priority Support</p>
            </div>
            <div className="text-center">
              <Badge className="text-lg px-4 py-2 bg-purple-300 text-black">Platinum</Badge>
              <p className="mt-2">20% + Exclusive Access</p>
            </div>
          </div>
          <Button size="lg" variant="outline" className="text-white border-white hover:bg-white hover:text-blue-600">
            Learn More
          </Button>
        </div>
      </section>
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product }) => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const handleAddToCart = () => {
    if (!user) {
      alert('Please login to add items to cart');
      return;
    }
    // Add to cart logic would go here
    alert('Added to cart!');
  };

  return (
    <Card className="group hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
      <CardContent className="p-0">
        <img 
          src={product.image_url} 
          alt={product.name}
          className="w-full h-48 object-cover rounded-t-lg group-hover:scale-105 transition-transform"
        />
        <div className="p-6">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-semibold line-clamp-2">{product.name}</h3>
            <Badge variant="outline">{product.brand}</Badge>
          </div>
          <p className="text-gray-600 text-sm mb-4 line-clamp-2">{product.description}</p>
          <div className="flex items-center justify-between mb-4">
            <span className="text-2xl font-bold text-blue-600">₹{product.price.toLocaleString()}</span>
            <div className="flex items-center space-x-1">
              <span className="text-yellow-400">★</span>
              <span className="text-sm font-medium">{product.rating}</span>
              <span className="text-sm text-gray-500">({product.review_count})</span>
            </div>
          </div>
          <div className="flex space-x-2">
            <Button 
              className="flex-1" 
              onClick={handleAddToCart}
              disabled={product.stock_quantity === 0}
            >
              {product.stock_quantity > 0 ? 'Add to Cart' : 'Out of Stock'}
            </Button>
            <Button variant="outline" size="sm">
              View Details
            </Button>
          </div>
          {user && (
            <div className="mt-2 text-xs text-green-600">
              Earn {Math.floor(product.price / 100)} loyalty points
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Products Page
const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await axios.get(`${API}/products?limit=50`);
        setProducts(response.data);
      } catch (error) {
        console.error('Error fetching products:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold mb-8">All Products</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </div>
    </div>
  );
};

// Loyalty Page
const LoyaltyPage = () => {
  const { user } = useAuth();
  const [loyaltyStatus, setLoyaltyStatus] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;

    const fetchData = async () => {
      try {
        const [loyaltyRes, ordersRes] = await Promise.all([
          axios.get(`${API}/loyalty/status`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          }),
          axios.get(`${API}/orders`, {
            headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
          })
        ]);
        
        setLoyaltyStatus(loyaltyRes.data);
        setOrders(ordersRes.data);
      } catch (error) {
        console.error('Error fetching loyalty data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Please Login</h1>
          <p className="text-gray-600">You need to be logged in to view your loyalty status</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="container mx-auto max-w-4xl">
        <h1 className="text-3xl font-bold mb-8">Loyalty Program</h1>
        
        {loyaltyStatus && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Your Loyalty Status</span>
                <Badge variant="outline" className="capitalize text-lg px-4 py-2">
                  {loyaltyStatus.tier}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">{loyaltyStatus.points}</div>
                  <div className="text-sm text-gray-600">Available Points</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">₹{loyaltyStatus.total_spent.toLocaleString()}</div>
                  <div className="text-sm text-gray-600">Total Spent</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">
                    {loyaltyStatus.benefits[loyaltyStatus.tier]?.discount || '0%'}
                  </div>
                  <div className="text-sm text-gray-600">Your Discount</div>
                </div>
              </div>
              
              <Separator className="my-6" />
              
              <h3 className="text-lg font-semibold mb-4">Tier Benefits</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(loyaltyStatus.benefits).map(([tier, benefits]) => (
                  <Card key={tier} className={`${loyaltyStatus.tier === tier ? 'ring-2 ring-blue-500' : ''}`}>
                    <CardContent className="p-4 text-center">
                      <Badge className={`mb-2 ${loyaltyStatus.tier === tier ? 'bg-blue-500' : 'bg-gray-400'}`}>
                        {tier}
                      </Badge>
                      <div className="space-y-1 text-sm">
                        <div>{benefits.discount} Discount</div>
                        {benefits.free_shipping && <div>Free Shipping</div>}
                        {benefits.priority_support && <div>Priority Support</div>}
                        {benefits.exclusive_access && <div>Exclusive Access</div>}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Recent Orders</CardTitle>
            <CardDescription>Your order history and points earned</CardDescription>
          </CardHeader>
          <CardContent>
            {orders.length === 0 ? (
              <p className="text-center text-gray-600 py-8">No orders yet. Start shopping to earn points!</p>
            ) : (
              <div className="space-y-4">
                {orders.slice(0, 5).map((order) => (
                  <div key={order.id} className="flex justify-between items-center p-4 border rounded-lg">
                    <div>
                      <div className="font-semibold">Order #{order.id.substring(0, 8)}</div>
                      <div className="text-sm text-gray-600">{new Date(order.created_at).toLocaleDateString()}</div>
                      <div className="text-sm">Status: <Badge variant="outline">{order.order_status}</Badge></div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold">₹{order.total_amount.toLocaleString()}</div>
                      <div className="text-sm text-green-600">+{order.loyalty_points_earned} points</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Categories Page
const CategoriesPage = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await axios.get(`${API}/categories`);
        setCategories(response.data);
      } catch (error) {
        console.error('Error fetching categories:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCategories();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen py-8 px-6">
      <div className="container mx-auto">
        <h1 className="text-3xl font-bold mb-8">Product Categories</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <Card key={category.id} className="group cursor-pointer hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2">
              <CardContent className="p-0">
                <img 
                  src={category.image_url || "https://images.unsplash.com/photo-1498049794561-7780e7231661"} 
                  alt={category.name}
                  className="w-full h-48 object-cover rounded-t-lg group-hover:scale-105 transition-transform"
                />
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-2">{category.name}</h3>
                  <p className="text-gray-600 mb-4">{category.description}</p>
                  <Button className="w-full">Browse Products</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="bg-gray-900 text-white py-12 px-6">
      <div className="container mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <div className="h-8 w-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-md flex items-center justify-center">
                <span className="text-white font-bold text-sm">EM</span>
              </div>
              <span className="text-xl font-bold">ElectroMart</span>
            </div>
            <p className="text-gray-400 text-sm">
              Your trusted destination for premium electronics with rewarding shopping experience.
            </p>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><Link to="/" className="hover:text-white transition-colors">Home</Link></li>
              <li><Link to="/products" className="hover:text-white transition-colors">Products</Link></li>
              <li><Link to="/categories" className="hover:text-white transition-colors">Categories</Link></li>
              <li><Link to="/loyalty" className="hover:text-white transition-colors">Loyalty Program</Link></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">Contact Us</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Help Center</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Shipping Info</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Returns</a></li>
            </ul>
          </div>
          
          <div>
            <h4 className="font-semibold mb-4">Payment Methods</h4>
            <div className="flex space-x-2 mb-4">
              <Badge variant="outline" className="text-xs">UPI</Badge>
              <Badge variant="outline" className="text-xs">PhonePe</Badge>
              <Badge variant="outline" className="text-xs">Paytm</Badge>
            </div>
            <p className="text-gray-400 text-sm">
              Secure payments with all major Indian payment apps
            </p>
          </div>
        </div>
        
        <Separator className="my-8 bg-gray-700" />
        
        <div className="text-center text-sm text-gray-400">
          <p>&copy; 2025 ElectroMart. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-background">
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/categories" element={<CategoriesPage />} />
            <Route path="/loyalty" element={<LoyaltyPage />} />
          </Routes>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;