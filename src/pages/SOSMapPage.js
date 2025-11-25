import React, { useState, useEffect } from 'react';
import { 
  Box, Button, Dialog, DialogTitle, DialogContent, DialogActions, 
  TextField, Typography, IconButton, CircularProgress, Snackbar 
} from '@material-ui/core';
import { Alert } from '@material-ui/lab'; 
import { Warning, PhotoCamera, Close, MyLocation } from '@material-ui/icons';
import { makeStyles } from '@material-ui/core/styles';
import { useNavigate } from 'react-router-dom';
import GoongSOSMap from '../GoongSOSMap';
import { reportSOS, getSOSAlerts } from '../api';

const useStyles = makeStyles((theme) => ({
  root: {
    height: 'calc(100vh - 64px)',
    position: 'relative',
    width: '100%',
  },
  floatingPanel: {
    position: 'absolute',
    bottom: theme.spacing(4),
    right: theme.spacing(2),
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    gap: theme.spacing(1),
  },
  sosBtn: {
    borderRadius: 30,
    padding: '12px 24px',
    fontWeight: 'bold',
    fontSize: '1rem',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    backgroundColor: '#d32f2f',
    color: 'white',
    '&:hover': {
      backgroundColor: '#b71c1c',
    },
    animation: '$pulse 2s infinite'
  },
  '@keyframes pulse': {
    '0%': { boxShadow: '0 0 0 0 rgba(211, 47, 47, 0.7)' },
    '70%': { boxShadow: '0 0 0 15px rgba(211, 47, 47, 0)' },
    '100%': { boxShadow: '0 0 0 0 rgba(211, 47, 47, 0)' },
  },
  // Nút định vị nhỏ
  locationBtn: {
    backgroundColor: 'white',
    color: '#333',
    marginBottom: 10,
    boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    '&:hover': { backgroundColor: '#f5f5f5' }
  }
}));

export default function SOSMapPage() {
  const classes = useStyles();
  const navigate = useNavigate();
  const [sosList, setSosList] = useState([]);
  const [userLocation, setUserLocation] = useState(null);
  
  // State Dialog
  const [openDialog, setOpenDialog] = useState(false);
  const [description, setDescription] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [loading, setLoading] = useState(false);

  // State Thông báo (Snackbar)
  const [notify, setNotify] = useState({ open: false, message: '', severity: 'info' }); // severity: success | error | warning | info

  // 1. Chỉ tải danh sách SOS (Không lấy vị trí user tự động nữa)
  const fetchSOS = async () => {
    try {
      const data = await getSOSAlerts();
      setSosList(data);
    } catch (e) {
      console.error("Lỗi tải SOS:", e);
    }
  };

  useEffect(() => {
    fetchSOS();
    const interval = setInterval(fetchSOS, 5000);
    return () => clearInterval(interval);
  }, []);

  // Hàm hiển thị thông báo đẹp
  const showMessage = (msg, type = 'info') => {
    setNotify({ open: true, message: msg, severity: type });
  };

  const handleCloseNotify = () => {
    setNotify({ ...notify, open: false });
  };

  // Hàm chủ động lấy vị trí (khi bấm nút)
  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      showMessage("Trình duyệt không hỗ trợ định vị", "error");
      return;
    }
    showMessage("Đang lấy vị trí của bạn...", "info");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude });
        showMessage("Đã cập nhật vị trí!", "success");
      },
      (err) => showMessage("Không thể lấy vị trí. Hãy bật GPS!", "error"),
      { enableHighAccuracy: true }
    );
  };

  // Mở Dialog báo cáo
  const handleOpenReport = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      showMessage("Bạn cần đăng nhập để gửi báo cáo!", "warning");
      setTimeout(() => navigate('/login'), 1500);
      return;
    }
    
    // Nếu chưa có vị trí thì tự động lấy
    if (!userLocation) {
      handleGetLocation();
    }
    setOpenDialog(true);
  };

  // Gửi báo cáo
  const handleSubmit = async () => {
    if (!userLocation) {
      showMessage("Chưa có tọa độ! Vui lòng đợi lấy vị trí.", "warning");
      handleGetLocation();
      return;
    }
    if (!description.trim()) {
      showMessage("Vui lòng nhập mô tả sự cố!", "error");
      return;
    }

    setLoading(true);
    try {
      await reportSOS(userLocation.lat, userLocation.lon, description, imageFile);
      showMessage("Gửi báo cáo thành công! Cảm ơn bạn.", "success");
      setOpenDialog(false);
      setDescription('');
      setImageFile(null);
      fetchSOS(); 
    } catch (err) {
      showMessage("Gửi thất bại: " + err.message, "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className={classes.root}>
      <GoongSOSMap 
        userLocation={userLocation} 
        sosAlerts={sosList} 
      />

      <div className={classes.floatingPanel}>
        {/* Nút định vị thủ công */}
        <Button 
           variant="contained" 
           className={classes.locationBtn}
           onClick={handleGetLocation}
        >
          <MyLocation />
        </Button>

        {/* Nút báo cáo SOS */}
        <Button 
          variant="contained" 
          className={classes.sosBtn}
          startIcon={<Warning />}
          onClick={handleOpenReport}
        >
          BÁO CÁO SỰ CỐ
        </Button>
      </div>

      {/* Dialog Nhập liệu */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="xs" fullWidth>
        <DialogTitle style={{ backgroundColor: '#d32f2f', color: 'white' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">🚨 Báo cáo khẩn cấp</Typography>
            <IconButton size="small" style={{ color: 'white' }} onClick={() => setOpenDialog(false)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          <Box display="flex" alignItems="center" mb={2} color="text.secondary">
            <MyLocation style={{ fontSize: 16, marginRight: 5 }} />
            <Typography variant="body2">
              {userLocation ? `${userLocation.lat.toFixed(5)}, ${userLocation.lon.toFixed(5)}` : 'Đang định vị...'}
            </Typography>
          </Box>

          <TextField
            autoFocus
            margin="dense"
            label="Mô tả hiện trường (Tai nạn, ngập, kẹt xe...)"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <Box mt={2}>
            <input
              accept="image/*"
              style={{ display: 'none' }}
              id="upload-sos-img"
              type="file"
              onChange={(e) => setImageFile(e.target.files[0])}
            />
            <label htmlFor="upload-sos-img">
              <Button variant="outlined" component="span" startIcon={<PhotoCamera />} fullWidth>
                {imageFile ? "Đã chọn 1 ảnh" : "Chụp ảnh hiện trường"}
              </Button>
            </label>
          </Box>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Hủy</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            style={{ backgroundColor: '#d32f2f', color: 'white' }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : "GỬI BÁO CÁO"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* COMPONENT THÔNG BÁO (SNACKBAR) */}
      <Snackbar 
        open={notify.open} 
        autoHideDuration={4000} 
        onClose={handleCloseNotify}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }} // Hiện ở trên cùng giữa
      >
        <Alert onClose={handleCloseNotify} severity={notify.severity} variant="filled">
          {notify.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}