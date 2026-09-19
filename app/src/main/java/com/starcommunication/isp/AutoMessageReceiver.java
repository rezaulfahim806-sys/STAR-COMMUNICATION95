package com.starcommunication.isp;

import android.Manifest;
import android.app.AlarmManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.telephony.SmsManager;
import android.net.Uri;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;

/** Automatic customer SMS receiver. Uses the phone SIM when SEND_SMS permission is granted. */
public class AutoMessageReceiver extends BroadcastReceiver {
    public static final String ACTION = "com.starcommunication.isp.AUTO_MESSAGE";
    public static final String TYPE = "type";
    public static final String PHONE = "phone";
    public static final String NAME = "name";
    public static final String CODE = "code", LOCATION="location", PKG="pkg", BILL="bill", PREV="prev";
    private static final String CHANNEL = "star_customer_messages";

    @Override public void onReceive(Context context, Intent intent) {
        if (intent == null) return;
        String phone = intent.getStringExtra(PHONE);
        String name = intent.getStringExtra(NAME);
        String type = intent.getStringExtra(TYPE);
        if (phone == null || phone.trim().isEmpty()) return;

        String customer = (name == null || name.trim().isEmpty()) ? "Customer" : name.trim();
        String msg;
        if ("expiry".equals(type)) {
            String code=intent.getStringExtra(CODE); String location=intent.getStringExtra(LOCATION); String pkg=intent.getStringExtra(PKG); String bill=intent.getStringExtra(BILL); String prev=intent.getStringExtra(PREV); String link="https://rezaulfahim806-sys.github.io/STAR-COMMUNICATION95/pay.html?code="+Uri.encode(code==null?"":code)+"&name="+Uri.encode(customer)+"&location="+Uri.encode(location==null?"-":location)+"&package="+Uri.encode(pkg==null?"":pkg)+"&bill="+Uri.encode(bill==null?"0":bill)+"&prev="+Uri.encode(prev==null?"0":prev); msg = "প্রিয় " + customer + ", আপনার ইন্টারনেট সংযোগের মেয়াদ শেষ হয়েছে। বিল পরিশোধ করতে Payment Link: " + link + " — STAR COMMUNICATION";
        } else {
            msg = "প্রিয় " + customer + ", নতুন মাসের ইন্টারনেট বিল শুরু হয়েছে। অনুগ্রহ করে সময়মতো বিল পরিশোধ করুন। — STAR COMMUNICATION";
        }

        boolean sent = sendSimSms(context, phone, msg);
        if (!sent) showReminder(context, customer, msg, phone);
        if ("month_end".equals(type)) scheduleMonthEnd(context, phone, name);
    }

    private static boolean sendSimSms(Context context, String phone, String msg) {
        try {
            if (Build.VERSION.SDK_INT >= 23 && context.checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) return false;
            SmsManager.getDefault().sendTextMessage(phone.trim(), null, msg, null, null);
            return true;
        } catch (Exception ignored) { return false; }
    }

    private static void showReminder(Context context, String name, String msg, String phone) {
        try {
            NotificationManager nm = (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
            if (nm == null) return;
            if (Build.VERSION.SDK_INT >= 26) nm.createNotificationChannel(new NotificationChannel(CHANNEL, "Customer Message Reminders", NotificationManager.IMPORTANCE_HIGH));
            Intent open = new Intent(context, MainActivity.class);
            open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
            PendingIntent pi = PendingIntent.getActivity(context, (phone + msg).hashCode(), open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            Notification.Builder builder = Build.VERSION.SDK_INT >= 26 ? new Notification.Builder(context, CHANNEL) : new Notification.Builder(context);
            builder.setSmallIcon(R.drawable.star_launcher).setContentTitle("STAR COMMUNICATION — SMS failed").setContentText(name + " এর জন্য SMS পাঠানো যায়নি").setStyle(new Notification.BigTextStyle().bigText(msg)).setAutoCancel(true).setContentIntent(pi);
            nm.notify((phone + msg).hashCode(), builder.build());
        } catch (Exception ignored) {}
    }

    public static void scheduleExpiry(Context c, String phone, String name, String expiry) { scheduleExpiry(c,phone,name,expiry,phone,"-","", "0","0"); }

    public static void scheduleExpiry(Context c, String phone, String name, String expiry, String code, String location, String pkg, String bill, String prevDue) {
        try {
            Date d = new SimpleDateFormat("yyyy-MM-dd", Locale.US).parse(expiry);
            if (d == null) return;
            Calendar cal = Calendar.getInstance(); cal.setTime(d); cal.add(Calendar.DAY_OF_MONTH, 1); cal.set(Calendar.HOUR_OF_DAY, 9); cal.set(Calendar.MINUTE, 0); cal.set(Calendar.SECOND, 0); cal.set(Calendar.MILLISECOND, 0);
            schedule(c, phone, name, "expiry", cal.getTimeInMillis(), code, location, pkg, bill, prevDue);
        } catch (Exception ignored) {}
    }

    public static void scheduleMonthEnd(Context c, String phone, String name) {
        Calendar cal = Calendar.getInstance();
        cal.set(Calendar.DAY_OF_MONTH, 1); cal.add(Calendar.MONTH, 1); cal.add(Calendar.DAY_OF_MONTH, -1); cal.set(Calendar.HOUR_OF_DAY, 20); cal.set(Calendar.MINUTE, 0); cal.set(Calendar.SECOND, 0); cal.set(Calendar.MILLISECOND, 0);
        if (cal.getTimeInMillis() <= System.currentTimeMillis()) { cal.add(Calendar.MONTH, 1); cal.set(Calendar.DAY_OF_MONTH, 1); cal.add(Calendar.MONTH, -1); }
        schedule(c, phone, name, "month_end", cal.getTimeInMillis());
    }

    public static void cancelExpiry(Context c,String phone){ try{ AlarmManager am=(AlarmManager)c.getSystemService(Context.ALARM_SERVICE); Intent i=new Intent(c,AutoMessageReceiver.class); i.setAction(ACTION); i.putExtra(PHONE,phone); i.putExtra(TYPE,"expiry"); int code=(phone+"expiry").hashCode(); PendingIntent pi=PendingIntent.getBroadcast(c,code,i,PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE); if(am!=null) am.cancel(pi); }catch(Exception ignored){} }

    private static void schedule(Context c, String phone, String name, String type, long when) { schedule(c,phone,name,type,when,phone,"-","", "0","0"); }
    private static void schedule(Context c, String phone, String name, String type, long when, String codeExtra, String locationExtra, String pkgExtra, String billExtra, String prevExtra) {
        if (when <= System.currentTimeMillis()) return;
        try {
            AlarmManager am = (AlarmManager) c.getSystemService(Context.ALARM_SERVICE); if (am == null) return;
            Intent i = new Intent(c, AutoMessageReceiver.class); i.setAction(ACTION); i.putExtra(PHONE, phone); i.putExtra(NAME, name); i.putExtra(TYPE, type); if("expiry".equals(type)){i.putExtra(CODE,codeExtra);i.putExtra(LOCATION,locationExtra);i.putExtra(PKG,pkgExtra);i.putExtra(BILL,billExtra);i.putExtra(PREV,prevExtra);}
            int code = (phone + type).hashCode(); PendingIntent pi = PendingIntent.getBroadcast(c, code, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            if (Build.VERSION.SDK_INT >= 23) { try { am.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, when, pi); } catch (SecurityException e) { am.set(AlarmManager.RTC_WAKEUP, when, pi); } }
            else am.setExact(AlarmManager.RTC_WAKEUP, when, pi);
        } catch (Exception ignored) {}
    }
}
