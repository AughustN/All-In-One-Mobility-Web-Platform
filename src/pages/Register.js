import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    makeStyles,
    Link,
    CircularProgress
} from '@material-ui/core';
import { Alert } from '@material-ui/lab';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { register } from '../api';

const useStyles = makeStyles((theme) => ({
    root: {
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: theme.spacing(2),
    },
    card: {
        maxWidth: 400,
        width: '100%',
        borderRadius: 16,
        boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        backdropFilter: 'blur(4px)',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        border: '1px solid rgba(255, 255, 255, 0.18)',
    },
    title: {
        fontWeight: 700,
        textAlign: 'center',
        marginBottom: theme.spacing(3),
        color: '#333',
    },
    form: {
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing(2),
    },
    submitButton: {
        marginTop: theme.spacing(2),
        height: 48,
        borderRadius: 24,
        background: 'linear-gradient(45deg, #FF512F 30%, #DD2476 90%)',
        color: 'white',
        boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
        '&:hover': {
            background: 'linear-gradient(45deg, #E64A19 30%, #C2185B 90%)',
        },
    },
    link: {
        textAlign: 'center',
        marginTop: theme.spacing(2),
    }
}));

export default function Register() {
    const classes = useStyles();
    const navigate = useNavigate();
    const [formData, setFormData] = useState({ username: '', password: '', confirmPassword: '' });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords don't match");
            return;
        }

        setLoading(true);
        setError('');

        try {
            await register(formData.username, formData.password);
            navigate('/login');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box className={classes.root}>
            <Card className={classes.card}>
                <CardContent style={{ padding: 32 }}>
                    <Typography variant="h4" className={classes.title}>
                        Create Account
                    </Typography>

                    {error && <Alert severity="error" style={{ marginBottom: 16 }}>{error}</Alert>}

                    <form className={classes.form} onSubmit={handleSubmit}>
                        <TextField
                            label="Username"
                            name="username"
                            variant="outlined"
                            fullWidth
                            required
                            value={formData.username}
                            onChange={handleChange}
                        />
                        <TextField
                            label="Password"
                            name="password"
                            type="password"
                            variant="outlined"
                            fullWidth
                            required
                            value={formData.password}
                            onChange={handleChange}
                        />
                        <TextField
                            label="Confirm Password"
                            name="confirmPassword"
                            type="password"
                            variant="outlined"
                            fullWidth
                            required
                            value={formData.confirmPassword}
                            onChange={handleChange}
                        />

                        <Button
                            type="submit"
                            variant="contained"
                            className={classes.submitButton}
                            disabled={loading}
                        >
                            {loading ? <CircularProgress size={24} color="inherit" /> : 'Sign Up'}
                        </Button>
                    </form>

                    <Box className={classes.link}>
                        <Typography variant="body2">
                            Already have an account?{' '}
                            <Link component={RouterLink} to="/login" color="primary" style={{ fontWeight: 600 }}>
                                Login
                            </Link>
                        </Typography>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
}
