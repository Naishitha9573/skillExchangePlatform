import {Navigate,useLocation} from 'react-router-dom'; import {useAuth} from '../context/AuthContext';
export default function Protected({children}){const {user}=useAuth();const loc=useLocation();return user?children:<Navigate to="/login" state={{from:loc}} replace/>}
