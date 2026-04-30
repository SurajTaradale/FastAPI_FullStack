import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import Cookies from 'js-cookie';

/**
 * PrivateRoute checks BOTH Redux state and the persisted cookie.
 * This handles page refreshes where Redux state resets but the cookie survives.
 */
const PrivateRoute = ({ component: Component, usertype }) => {
  const isAgentAuthenticated = useSelector((state) => state.agent.isAgentAuthenticated);
  const isCustomerAuthenticated = useSelector((state) => state.customer.isCustomerAuthenticated);

  if (usertype === 'agent') {
    const hasToken = isAgentAuthenticated || !!Cookies.get('agent_token');
    return hasToken ? <Component /> : <Navigate to="/agent/login" replace />;
  }

  if (usertype === 'customer') {
    const hasToken = isCustomerAuthenticated || !!Cookies.get('customeruser_token');
    return hasToken ? <Component /> : <Navigate to="/customer/login" replace />;
  }

  // Unknown usertype — redirect to agent login as safe fallback
  return <Navigate to="/agent/login" replace />;
};

export default PrivateRoute;
