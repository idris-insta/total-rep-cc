import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Factory } from 'lucide-react';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        toast.success('Login successful!');
      } else {
        await register(email, password, name, 'user');
        toast.success('Registration successful!');
      }
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="flex items-center justify-center mb-8">
            <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-accent to-orange-600 flex items-center justify-center">
              <Factory className="h-8 w-8 text-white" strokeWidth={2} />
            </div>
          </div>
          
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-slate-900 font-manrope">AdhesiveFlow ERP</h1>
            <p className="text-slate-600 mt-2 font-inter">Industrial Precision Management</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm font-semibold text-slate-700 font-inter">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  required={!isLogin}
                  className="h-11 font-inter"
                  data-testid="name-input"
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-semibold text-slate-700 font-inter">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="h-11 font-inter"
                data-testid="email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-semibold text-slate-700 font-inter">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="h-11 font-inter"
                data-testid="password-input"
              />
            </div>

            <Button
              type="submit"
              className="w-full h-11 bg-accent hover:bg-accent/90 text-white font-semibold shadow-lg hover:shadow-accent/20 transition-all font-inter"
              disabled={loading}
              data-testid="submit-button"
            >
              {loading ? 'Please wait...' : isLogin ? 'Login' : 'Register'}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-accent hover:text-accent/80 font-medium font-inter"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? "Don't have an account? Register" : 'Already have an account? Login'}
            </button>
          </div>
        </div>

        <p className="text-center text-slate-400 text-sm mt-6 font-inter">
          Powered by AdhesiveFlow - Industrial ERP Suite
        </p>
      </div>
    </div>
  );
};

export default Login;